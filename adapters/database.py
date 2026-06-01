import os
import json
import sqlite3
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from adapters.base import EmissionEvent

logger = logging.getLogger("mirkwood.database")


class DatabaseStore:
    """Production-grade database store supporting SQLite and standard SQL structures.
    Uses sqlite3 locally as a fallback, but is structured to easily integrate with PostgreSQL.
    """

    def __init__(self, db_path: str = "mirkwood.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        # Enables JSON1 extension features in newer SQLite releases automatically
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the emission_events table if it does not exist."""
        query = """
        CREATE TABLE IF NOT EXISTS emission_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            ingest_timestamp TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            accuracy_m REAL,
            location_source TEXT,
            geohash TEXT,
            channel_type TEXT NOT NULL,
            source_tool TEXT NOT NULL,
            primary_id TEXT,
            secondary_ids TEXT, -- JSON array string locally
            device_fingerprint TEXT,
            metadata TEXT NOT NULL DEFAULT '{}', -- JSON string
            observed_duration TEXT,
            session_id TEXT,
            tags TEXT, -- JSON array string locally
            enrichment TEXT NOT NULL DEFAULT '{}' -- JSON string
        );
        """
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON emission_events(timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_events_fingerprint ON emission_events(device_fingerprint);",
            "CREATE INDEX IF NOT EXISTS idx_events_primary_id ON emission_events(primary_id);",
            "CREATE INDEX IF NOT EXISTS idx_events_channel_tool ON emission_events(source_tool, timestamp DESC);"
        ]

        conn = self._get_connection()
        try:
            conn.execute(query)
            for index_query in indexes:
                conn.execute(index_query)
            conn.commit()
        finally:
            conn.close()
        logger.info(f"Database initialized successfully at: {os.path.abspath(self.db_path)}")

    def insert_events(self, events: List[EmissionEvent]) -> int:
        """Inserts a batch of EmissionEvents into the database."""
        if not events:
            return 0

        query = """
        INSERT INTO emission_events (
            event_id, timestamp, ingest_timestamp, latitude, longitude, accuracy_m,
            location_source, geohash, channel_type, source_tool, primary_id,
            secondary_ids, device_fingerprint, metadata, observed_duration,
            session_id, tags, enrichment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        records = []
        for e in events:
            # Format timestamps to ISO strings
            ts_str = e.timestamp.isoformat() if isinstance(e.timestamp, datetime) else str(e.timestamp)
            ingest_ts_str = datetime.utcnow().isoformat()

            records.append((
                str(e.event_id),
                ts_str,
                ingest_ts_str,
                e.latitude,
                e.longitude,
                e.accuracy_m,
                e.location_source,
                getattr(e, 'geohash', None),
                e.channel_type,
                e.source_tool,
                e.primary_id,
                json.dumps(e.secondary_ids),
                e.device_fingerprint,
                json.dumps(e.metadata),
                e.observed_duration,
                e.session_id,
                json.dumps(e.tags),
                json.dumps(e.enrichment)
            ))

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, records)
            conn.commit()
            row_count = cursor.rowcount
        finally:
            conn.close()
            
        logger.debug(f"Successfully inserted {row_count} events into database.")
        return row_count

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Utility method to fetch recent events for validation or reporting."""
        query = "SELECT * FROM emission_events ORDER BY timestamp DESC LIMIT ?"
        conn = self._get_connection()
        try:
            rows = conn.execute(query, (limit,)).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

