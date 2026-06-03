Mirkwood
A synthetic research platform for demonstrating cross-channel pseudonymity collapse through passive RF observation.
> "To see is to be bound."  
> Per-channel anonymity is deniable. The joint distribution is not.
---
Purpose
Mirkwood is a research instrument that demonstrates how multiple independent wireless channels — observed together — defeat pseudonymity without breaking any single protocol's encryption.
It fuses emissions from:
Public safety trunked radio (P25/EDACS)
LoRa mesh networks
BLE/IoT devices
WiFi & Bluetooth
SIP/VoIP signaling
LTE control plane
Rogue cell detection
All data feeding the published pipeline is strictly synthetic, produced by a physically contained lab. The capture hardware bill of materials, firmware, frequencies, and calibration data are withheld. See `DISCLAIMER.md` for scope boundaries and prohibited uses.
---
Architecture
Mirkwood has three layers.
Capture — Independent sensor nodes inside a contained RF lab. Not reproduced here. See `architecture.md` for the structural description; the BOM and firmware are withheld by design.
Ingestion — A production-grade async Python daemon (`IngestionPipeline`) with three concurrent ingest paths: directory watching, TCP socket streaming (port 8900 default), and stdin piping. All events are normalized to a unified `EmissionEvent` schema and persisted to SQLite via `DatabaseStore`. Seven per-tool adapters handle format translation and stable cross-channel fingerprinting.
Analysis — `MirkwoodAnalyst` accepts natural language questions, generates read-only SQLite SELECT queries via a schema-in-prompt LLM call, executes them, and renders results to the terminal alongside the generated SQL. The escape hatch is `CANNOT_ANSWER`. No RAG, no agent framework, no vector store. One call per question.
The full architectural reasoning for each layer — including why heavier stacks were rejected — is in `architecture.md`.
---
Integrated Tools
Tool	Purpose	Channel	Status
BearSentinel	BCD325P2 trunked radio telemetry	P25 / EDACS	Integrated
MeshNarc	Passive Meshtastic SIGINT	LoRa Mesh	Integrated
rfparty-xyz	BLE situational awareness	Bluetooth Low Energy	Integrated
wardriver_rev3	WiFi + BT wardriving	802.11 / BT	Integrated
pocket-dial	Lightweight SIP PBX	VoIP Signaling	Integrated
LTESniffer	RTL-SDR LTE downlink	LTE Control Plane	Integrated
Rayhunter	EFF rogue cell / IMSI-catcher detector	Cellular Surveillance	Integrated
---
Core Schema
All data normalizes to a single `EmissionEvent` (see `EmissionEvent_Schema.md`):
`timestamp`, `latitude`, `longitude`, `channel_type`, `source_tool`
`primary_id`, `secondary_ids`
`device_fingerprint` — stable SHA-256 cross-channel identifier
`metadata` — protocol-specific JSON
`tags`, `enrichment` (WiGLE, OUI, AgencyDB)
Cross-channel correlation is a spatiotemporal join on `device_fingerprint` and `timestamp` across rows from different `channel_type` values. The schema is the methodology.
---
Usage
Install dependencies:
```bash
pip install -r requirements.txt
```
Run the ingestion daemon:
```bash
# Directory watcher + TCP server (default)
python -m adapters.pipeline --db mirkwood.db --port 8900

# Also accept stdin
python -m adapters.pipeline --stdin

# Print DB statistics and exit
python -m adapters.pipeline --stats
```
Query the database in natural language:
```bash
export GEMINI_API_KEY="..."
python -m adapters.analyst_cli "Find all BLE beacons observed within 500m of a P25 grant in the same 5-minute window" --db mirkwood.db
```
Run the test suite:
```bash
python tests/test_adapters.py
```
---
Repository Structure
```
├── adapters/
│   ├── __init__.py             # Package exports
│   ├── base.py                 # GeoPoint, EmissionEvent, NormalizationAdapter
│   ├── bcd325p2.py             # BearSentinel adapter (P25 / EDACS)
│   ├── meshnarc.py             # MeshNarc adapter (LoRa Mesh)
│   ├── rfparty.py              # rfparty adapter (BLE)
│   ├── wardriver.py            # wardriver_rev3 adapter (WiFi + BT)
│   ├── pocket_dial.py          # pocket-dial adapter (SIP/VoIP)
│   ├── lte_sniffer.py          # LTESniffer adapter (LTE control plane)
│   ├── rayhunter.py            # Rayhunter adapter (rogue cell / IMSI catcher)
│   ├── mirkwood_normalizer.py  # Adapter router
│   ├── database.py             # SQLite store (DatabaseStore)
│   ├── pipeline.py             # Async ingestion daemon (IngestionPipeline)
│   ├── analyst.py              # NL-to-SQL analyst (MirkwoodAnalyst)
│   └── analyst_cli.py          # Terminal interface
├── tests/
│   └── test_adapters.py        # Full adapter + DB + analyst validation suite
├── DISCLAIMER.md               # Scope, false-positive statement, prohibited uses
├── EmissionEvent_Schema.md     # Unified schema definition
├── architecture.md             # Architectural decisions, layer rationale
├── mirkwood.png                # System diagram
├── requirements.txt
└── README.md
```
---
Project Status
The ingestion pipeline, normalization adapters, database layer, and analyst interface are functional and test-passing. The capture layer — hardware BOM, firmware, RF containment setup, and synthetic scenario generator — is not published and will not be. That boundary is described in `DISCLAIMER.md` and is enforced by omission, not by software policy.
This is a research instrument. It is not a product, a field kit, or a starting point for operational construction. The withheld components are the reproduction path. What is here demonstrates the methodology; what is absent is what makes the methodology runnable against real data.
---
Read Before Using
`DISCLAIMER.md` covers: what the project is and is not, the false-positive problem stated plainly, the bidirectionality problem, the worked example of the hardest application case, legal exposure, and the synthetic envelope as a permanent operating boundary — not a temporary convenience.
That document exists so any future reader encounters the project's own framing first.
