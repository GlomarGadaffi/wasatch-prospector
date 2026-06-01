import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, List, Optional
from adapters.database import DatabaseStore

logger = logging.getLogger("mirkwood.analyst")


class MirkwoodAnalyst:
    """Headless AI Analyst for Mirkwood. Converts natural language to SQLite queries
    using Gemini, executes them, and returns structured results.
    Reflects the 'Talk to the logs' architecture of CDRChat but tailored for Mirkwood's fused DB.
    """

    def __init__(self, db_path: str = "mirkwood.db", api_key: Optional[str] = None):
        self.db = DatabaseStore(db_path)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def _get_schema_prompt(self) -> str:
        """Serializes the exact SQLite schema of the emission_events table for prompt injection."""
        return """
TABLE: emission_events
COLUMNS:
  - event_id (TEXT, Primary Key, UUID string)
  - timestamp (TEXT, ISO 8601 UTC string format: 'YYYY-MM-DDTHH:MM:SS.mmmmmm')
  - ingest_timestamp (TEXT, ISO 8601 UTC string)
  - latitude (REAL, latitude in decimal degrees)
  - longitude (REAL, longitude in decimal degrees)
  - accuracy_m (REAL, accuracy in meters)
  - location_source (TEXT, source of location data e.g. GPS, wardriver)
  - geohash (TEXT)
  - channel_type (TEXT, e.g. 'P25_TRUNK', 'MESHTASTIC', 'BLE', 'WIFI', 'BT', 'SIP', 'LTE_SNIFFER', 'IMSI_CATCHER_DETECT')
  - source_tool (TEXT, e.g. 'BearSentinel', 'MeshNarc', 'rfparty', 'wardriver_rev3', 'pocket-dial', 'LTESniffer', 'Rayhunter')
  - primary_id (TEXT, main identifier: UnitID, MAC, BSSID, Mesh Node ID, SIP Extension, Cell ID)
  - secondary_ids (TEXT, JSON array string representing list of related IDs: e.g. '["talkgroup_id"]' or '["tmsi", "imsi"]')
  - device_fingerprint (TEXT, stable SHA-256 cross-channel hash representing a single physical target/MAC)
  - metadata (TEXT, JSON string containing protocol-specific rich data fields)
  - observed_duration (TEXT, ISO 8601 duration)
  - session_id (TEXT, session tracking ID like call_id)
  - tags (TEXT, JSON array string representing list of tags: e.g. '["wifi"]', '["rogue", "cellular"]')
  - enrichment (TEXT, JSON string)
"""

    def _call_gemini_rest(self, system_prompt: str, user_prompt: str) -> str:
        """Fallback REST caller for Gemini. Zero external dependencies, extremely robust."""
        if not self.api_key:
            raise ValueError("Missing Gemini API Key. Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

        # We use gemini-2.5-flash as the standard, high-performance model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        headers = {"Content-Type": "application/json"}
        
        # Structure the payload in standard Google AI Developer API format
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\nUser Question: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,  # Zero temperature for deterministic SQL generation
                "maxOutputTokens": 1024
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                
                # Extract text from standard response structure
                candidates = resp_data.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                    return text.strip()
                raise ValueError("Empty response received from Gemini API.")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API request failed: {e.code} - {error_body}")
        except Exception as e:
            raise RuntimeError(f"Connection to Gemini API failed: {e}")

    def generate_sql(self, question: str) -> str:
        """Converts user's natural language question into valid SQLite query using the cached schema."""
        schema_text = self._get_schema_prompt()
        
        system_prompt = f"""You are a professional database analyst for the Mirkwood RF/VoIP Spatiotemporal surveillance platform.
Your task is to convert the user's natural language question into a valid, safe SQLite SELECT query against the `emission_events` table.

---
{schema_text}
---

DIALECT & QUERY CONSTRAINTS:
1. Generate standard SQLite compatible SQL only.
2. Return ONLY the naked SQL query. Do NOT wrap it in markdown block tags (no ```sql or ```). Do not include any explanations, preambles, or postambles.
3. If the query requires checking JSON fields in metadata, use SQLite JSON functions e.g. `json_extract(metadata, '$.talkgroup_id')`.
4. If a query requires matching secondary_ids or tags, remember they are stored as JSON array strings. Use `json_each` or `LIKE '%"value"%'` or similar JSON array match.
   For example, to find tag 'wifi': `tags LIKE '%"wifi"%'` or `exists(select 1 from json_each(tags) where value = 'wifi')`.
5. Limit result set to a maximum of 100 rows unless explicitly specified.
6. The query MUST be read-only (SELECT statement only).
7. If the question cannot be answered using the provided schema, return the literal string `CANNOT_ANSWER`.

EXAMPLE:
Question: "Find all MeshNarc packets that have coordinates"
SQL: SELECT * FROM emission_events WHERE source_tool = 'MeshNarc' AND latitude IS NOT NULL AND longitude IS NOT NULL LIMIT 100

Question: "How many BLE beacons were observed in total?"
SQL: SELECT COUNT(*) as total_ble FROM emission_events WHERE channel_type = 'BLE'

Now translate the user's question.
"""
        raw_output = self._call_gemini_rest(system_prompt, question)
        
        # Clean up any residual markdown formatting from the LLM just in case
        cleaned_sql = raw_output.replace("```sql", "").replace("```", "").strip()
        
        # Check escape hatch
        if "CANNOT_ANSWER" in cleaned_sql:
            return "CANNOT_ANSWER"
            
        return cleaned_sql

    def query(self, question: str) -> Dict[str, Any]:
        """Runs the natural language query pipeline: Question -> SQL -> Execution -> Results."""
        logger.info(f"Analyzing question: '{question}'")
        
        sql = self.generate_sql(question)
        if sql == "CANNOT_ANSWER":
            logger.warning("AI Analyst determined the question cannot be answered from the available schema.")
            return {
                "question": question,
                "sql": None,
                "success": False,
                "error": "The question is out of scope or cannot be answered using the emission_events schema.",
                "results": []
            }
            
        logger.info(f"Generated SQL Query: {sql}")
        
        # Safety enforcement: ensure it is a SELECT statement
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            logger.error(f"Safety violation: generated non-SELECT statement: '{sql}'")
            return {
                "question": question,
                "sql": sql,
                "success": False,
                "error": "Security check failed: Only read-only SELECT statements are permitted.",
                "results": []
            }

        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            logger.info(f"Query executed successfully. Returned {len(results)} rows.")
            return {
                "question": question,
                "sql": sql,
                "success": True,
                "error": None,
                "results": results
            }
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "question": question,
                "sql": sql,
                "success": False,
                "error": f"Database execution error: {e}",
                "results": []
            }
        finally:
            conn.close()
