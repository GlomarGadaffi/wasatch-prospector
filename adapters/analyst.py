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


def classify_epistemic_status(sql: Optional[str]) -> Optional[Dict[str, Any]]:
    """Classify the epistemic standing of a generated query's result set.

    This is the structural counterpart to EVIDENTIARY.md: the honesty about what
    Mirkwood output *is* must travel WITH the output, not live only in a document
    a reader can skip. Every result the analyst returns is tagged, and the tag is
    rendered above the rows by the CLI so no consumer can mistake a hypothesis for
    a fact.

    Two tiers:
      * CORRELATION_HYPOTHESIS — the query correlates across rows (a self-join, an
        explicit JOIN, or any cross-row pairing on device_fingerprint / channel /
        spatiotemporal window). Each output row is a CO-PRESENCE HYPOTHESIS. Under
        realistic device density these are dominated by coincidence (see the base
        rate in EVIDENTIARY.md). NEVER an identification.
      * OBSERVATION — a single-table read of raw emissions. A record of what was
        received on the wire. A pseudonym is not a person.

    Neither tier is evidence of identity. `is_evidence` is always False.
    Returns None when there is no SQL to classify (e.g. CANNOT_ANSWER).
    """
    if not sql:
        return None

    s = " ".join(sql.upper().split())
    table_refs = s.count("EMISSION_EVENTS")
    correlates = (" JOIN " in s) or (table_refs >= 2)

    if correlates:
        status = "CORRELATION_HYPOTHESIS"
        caveat = (
            "This result set was produced by a cross-channel / spatiotemporal "
            "correlation. Each row pairs pseudonyms that share a fingerprint or a "
            "location-time window. That is a CO-PRESENCE HYPOTHESIS, not an "
            "identification of any person. Under realistic device density the "
            "false-positive rate is high. Treat every row as a lead to be "
            "independently verified under lawful process -- never as proof of "
            "identity, affiliation, or presence."
        )
    else:
        status = "OBSERVATION"
        caveat = (
            "This result set reports raw observed emissions (per-channel "
            "pseudonyms, locations, timestamps). An observation is a record of "
            "what was received on the wire, NOT an attribution to a named person. "
            "A pseudonym is not an identity."
        )

    return {
        "status": status,
        "is_evidence": False,
        "classification": "INVESTIGATIVE LEAD -- NOT EVIDENCE OF IDENTITY",
        "caveat": caveat,
        "reference": "EVIDENTIARY.md",
    }


class MirkwoodAnalyst:
    """Headless AI Analyst for Mirkwood. Converts natural language to SQLite queries
    using Gemini, executes them, and returns structured results.
    Reflects the 'Talk to the logs' architecture of CDRChat but tailored for Mirkwood's fused DB.
    """

    def __init__(self, db_path: str = "mirkwood.db", api_key: Optional[str] = None):
        self.db = DatabaseStore(db_path)
        self.db_path = db_path  # query() opens its own read-only connection against this path
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
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }
        
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
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        raise ValueError("Gemini API returned a candidate with no parts (likely safety-filtered).")
                    return parts[0].get("text", "").strip()
                raise ValueError("Empty response received from Gemini API.")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API request failed with status {e.code}: {error_body}")
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
                "results": [],
                "epistemic": None
            }
            
        logger.info(f"Generated SQL Query: {sql}")

        # First-pass guard: reject obvious non-SELECT statements before hitting the DB.
        # Real enforcement is the read-only connection below; this is defence-in-depth only.
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
            logger.error(f"Safety violation: generated non-SELECT statement.")
            return {
                "question": question,
                "sql": sql,
                "success": False,
                "error": "Security check failed: Only read-only SELECT statements are permitted.",
                "results": [],
                "epistemic": None
            }

        # Open a read-only connection so the SQLite engine itself enforces no writes,
        # regardless of CTE tricks, PRAGMA writes, or ATTACH attempts.
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to open read-only DB connection: {e}")
            return {
                "question": question,
                "sql": sql,
                "success": False,
                "error": f"Database connection error: {e}",
                "results": [],
                "epistemic": None
            }

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
                "results": results,
                "epistemic": classify_epistemic_status(sql)
            }
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "question": question,
                "sql": sql,
                "success": False,
                "error": f"Database execution error: {e}",
                "results": [],
                "epistemic": classify_epistemic_status(sql)
            }
        finally:
            conn.close()
