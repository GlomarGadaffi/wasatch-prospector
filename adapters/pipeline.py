import os
import sys
import json
import time
import socket
import select
import signal
import argparse
import asyncio
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List

# Ensure package root is importable when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adapters.base import EmissionEvent
from adapters.mirkwood_normalizer import MirkwoodNormalizer
from adapters.database import DatabaseStore

# Setup structured production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mirkwood_pipeline.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("mirkwood.pipeline")

# Graceful shutdown flag
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}. Initiating graceful shutdown...")
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(shutdown_event.set)


class IngestionPipeline:
    """Production-grade headless ingestion pipeline. Watches folders, listens on network sockets,
    and accepts piped STDIN inputs to normalize and persist RF/VoIP telemetry on the fly.
    """

    def __init__(self, db_path: str = "mirkwood.db", incoming_dir: str = "data/incoming", archive_dir: str = "data/archive"):
        self.db = DatabaseStore(db_path)
        self.normalizer = MirkwoodNormalizer()
        self.incoming_dir = incoming_dir
        self.archive_dir = archive_dir
        
        # Ensure directories exist
        os.makedirs(self.incoming_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    async def ingest_payload(self, source_tool: str, raw_payload: Any) -> int:
        """Helper to process and insert raw payload via the appropriate adapter."""
        try:
            events = await self.normalizer.process(source_tool, raw_payload)
            if events:
                inserted = self.db.insert_events(events)
                logger.info(f"Ingested {inserted} event(s) from tool: '{source_tool}'")
                return inserted
            else:
                logger.warning(f"Adapter for '{source_tool}' produced 0 normalized events from input.")
        except Exception as e:
            logger.error(f"Failed to ingest raw payload from '{source_tool}': {e}", exc_info=True)
        return 0

    async def start_directory_watcher(self, interval_seconds: float = 2.0):
        """Headless loop that watches folders for new raw JSON uploads."""
        logger.info(f"Directory Watcher started. Monitoring folder: {os.path.abspath(self.incoming_dir)}")
        
        while not shutdown_event.is_set():
            try:
                # Expect subdirectories or direct json files per tool: e.g. data/incoming/MeshNarc/*.json
                for file_name in os.listdir(self.incoming_dir):
                    file_path = os.path.join(self.incoming_dir, file_name)
                    
                    if not os.path.isfile(file_path) or not file_name.endswith('.json'):
                        continue
                    
                    logger.info(f"Detected incoming file: {file_name}")
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Files are expected to contain a "source_tool" key and the "payload"
                        # E.g. {"source_tool": "MeshNarc", "payload": {...}}
                        source_tool = data.get("source_tool")
                        payload = data.get("payload")
                        
                        if source_tool and payload is not None:
                            inserted = await self.ingest_payload(source_tool, payload)
                            if inserted > 0:
                                # Archive file on success
                                archive_path = os.path.join(self.archive_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}")
                                shutil.move(file_path, archive_path)
                                logger.info(f"File archived to: {archive_path}")
                        else:
                            logger.error(f"Invalid file format in {file_name}. Missing 'source_tool' or 'payload' keys.")
                            shutil.move(file_path, os.path.join(self.archive_dir, f"error_{file_name}"))
                    except Exception as e:
                        logger.error(f"Error parsing file {file_name}: {e}")
                        # Move to archive with error prefix
                        if os.path.exists(file_path):
                            shutil.move(file_path, os.path.join(self.archive_dir, f"error_{file_name}"))
            except Exception as e:
                logger.error(f"Directory watcher error: {e}")
                
            await asyncio.sleep(interval_seconds)

    async def start_socket_server(self, host: str = "127.0.0.1", port: int = 8900):
        """Headless socket listener that acts as a real-time TCP ingestion server."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setblocking(False)
        
        try:
            server.bind((host, port))
            server.listen(10)
            logger.info(f"Ingestion TCP server listening on tcp://{host}:{port}")
        except Exception as e:
            logger.critical(f"Failed to bind socket server to {host}:{port}: {e}")
            return

        loop = asyncio.get_event_loop()
        
        async def handle_client(reader, writer):
            peer = writer.get_extra_info('peername')
            logger.info(f"Connection accepted from client: {peer}")
            buffer = ""
            
            try:
                while not shutdown_event.is_set():
                    data = await reader.read(4096)
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8')
                    # Expect newline terminated JSON payloads (JSON Lines format)
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            payload_obj = json.loads(line)
                            source_tool = payload_obj.get("source_tool")
                            payload = payload_obj.get("payload")
                            
                            if source_tool and payload is not None:
                                await self.ingest_payload(source_tool, payload)
                            else:
                                logger.warning(f"TCP client sent invalid payload format: '{line}'")
                        except json.JSONDecodeError:
                            logger.error(f"TCP client sent invalid JSON packet: '{line}'")
            except Exception as e:
                logger.error(f"TCP socket handler error: {e}")
            finally:
                writer.close()
                logger.info(f"Connection closed for client: {peer}")

        async def accept_connections():
            while not shutdown_event.is_set():
                try:
                    conn, addr = await loop.sock_accept(server)
                    reader, writer = await asyncio.open_connection(sock=conn)
                    asyncio.create_task(handle_client(reader, writer))
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Socket accept error: {e}")
                    await asyncio.sleep(0.5)

        accept_task = asyncio.create_task(accept_connections())
        await shutdown_event.wait()
        
        # Cleanup
        accept_task.cancel()
        server.close()
        logger.info("TCP socket server shutdown complete.")

    async def start_stdin_reader(self):
        """Allows direct terminal pipelining of JSON streams."""
        logger.info("STDIN listener active. Pipeline is reading from standard input stream...")
        loop = asyncio.get_event_loop()
        
        # Set stdin non-blocking
        os.set_blocking(sys.stdin.fileno(), False)
        
        buffer = ""
        while not shutdown_event.is_set():
            try:
                # Use standard select to check if stdin has data
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                if ready:
                    data = sys.stdin.read()
                    if not data: # EOF
                        logger.info("STDIN stream closed (EOF reached).")
                        break
                    
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            payload_obj = json.loads(line)
                            source_tool = payload_obj.get("source_tool")
                            payload = payload_obj.get("payload")
                            if source_tool and payload is not None:
                                await self.ingest_payload(source_tool, payload)
                        except Exception as e:
                            logger.error(f"STDIN ingestion line error: {e}")
            except Exception as e:
                logger.error(f"STDIN loop error: {e}")
                
            await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser(description="Mirkwood Ingestion Engine - Headless Production Daemon")
    parser.add_argument("--db", type=str, default="mirkwood.db", help="Path to SQLite database file")
    parser.add_argument("--incoming", type=str, default="data/incoming", help="Folder to watch for incoming JSON uploads")
    parser.add_argument("--archive", type=str, default="data/archive", help="Folder to archive processed inputs")
    parser.add_argument("--port", type=int, default=8900, help="TCP port to listen on for stream ingestion")
    parser.add_argument("--stdin", action="store_true", help="Read raw JSON lines stream from STDIN")
    parser.add_argument("--stats", action="store_true", help="Print database statistics and exit")
    
    args = parser.parse_args()

    # If stats is passed, print stats and exit immediately
    if args.stats:
        db = DatabaseStore(args.db)
        events = db.get_recent_events(5)
        conn = db._get_connection()
        total_count = conn.execute("SELECT count(*) FROM emission_events").fetchone()[0]
        tools_summary = conn.execute("SELECT source_tool, count(*) FROM emission_events GROUP BY source_tool").fetchall()
        
        print("-" * 60)
        print(f"MIRKWOOD DATABASE STATISTICS ({os.path.abspath(args.db)})")
        print("-" * 60)
        print(f"Total Normalized Events: {total_count}")
        print("\nEvents per Ingested Tool:")
        for row in tools_summary:
            print(f" - {row[0]}: {row[1]} events")
        
        print("\nLast 5 Ingested Events:")
        for idx, event in enumerate(events, 1):
            print(f" {idx}. [{event['timestamp']}] {event['source_tool']} ({event['channel_type']}) | ID: {event['primary_id']}")
        print("-" * 60)
        return

    # Setup signal handlers for standard POSIX environments (Graceful shutdown)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, signal_handler)
        except ValueError:
            pass # Skip if not run in main thread (Windows compatibility issues for some signals)

    # Initialize and start pipeline components
    pipeline = IngestionPipeline(args.db, args.incoming, args.archive)
    
    tasks = [
        asyncio.create_task(pipeline.start_directory_watcher()),
        asyncio.create_task(pipeline.start_socket_server(port=args.port))
    ]
    
    if args.stdin:
        tasks.append(asyncio.create_task(pipeline.start_stdin_reader()))

    logger.info("Mirkwood Production Daemon successfully started! Press Ctrl+C to terminate.")
    
    # Wait for the shutdown event to trigger
    await shutdown_event.wait()
    
    logger.info("Stopping all background services...")
    for t in tasks:
        t.cancel()
        
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Mirkwood Daemon terminated gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
