# Mirkwood

> *"To see is to be bound."*
> Per-channel anonymity is deniable. The joint distribution is not.

A synthetic research platform demonstrating cross-channel pseudonymity collapse through passive RF observation.

**All data feeding the published pipeline is strictly synthetic.** The capture hardware bill of materials, firmware, frequencies, and calibration data are withheld. See [`DISCLAIMER.md`](DISCLAIMER.md) for scope boundaries and prohibited uses.

---

## The Core Claim

Every wireless protocol Mirkwood monitors has its own anonymity model. P25 uses logical unit IDs. Meshtastic uses rotating node IDs. BLE implements MAC randomization. LTE uses TMSI. SIP uses extension numbers. Each protocol's designers were correct that their individual channel resists identification by a single-channel observer.

The error is treating the channels as independent.

A device present at location $L$ at time $T$ emits signals on multiple channels simultaneously. Those signals share a spatial and temporal origin. The intersection of their pseudonyms — none of which individually identifies the device — collectively identifies it.

### Pseudonymity Collapse

Let $\text{ID}_k$ denote the pseudonym a device presents on channel $k$. For a single channel:

$$P(\text{identify} \mid \text{ID}_k) \approx 0$$

Under joint observation across $n$ channels, the posterior probability of identification given co-presence evidence is:

$$P(\text{identify} \mid \text{ID}_1, \text{ID}_2, \ldots, \text{ID}_n, \, L, \, T) \rightarrow 1 \text{ as } n \text{ grows}$$

The rate at which it converges depends on population density at $(L, T)$. This is the false positive problem — see below.

---

## Architecture

Mirkwood has three layers.

```
┌──────────────────────────────────────────────────────────────────┐
│                        CAPTURE LAYER                             │
│  BearSentinel (P25/EDACS)   MeshNarc (LoRa)   rfparty (BLE)    │
│  wardriver_rev3 (WiFi/BT)   pocket-dial (SIP)                   │
│  LTESniffer (LTE)           Rayhunter (rogue cell)              │
│                                                                  │
│  [ Hardware BOM, firmware, RF containment: withheld by design ]  │
└─────────────────────────────┬────────────────────────────────────┘
                              │  raw JSON per source_tool
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER                            │
│  MirkwoodNormalizer → per-adapter normalize() + fingerprint()    │
│  IngestionPipeline: directory watcher / TCP :8900 / stdin        │
│  DatabaseStore → SQLite (4 indexes; read-only URI for analyst)   │
│                                                                  │
│  All events → unified EmissionEvent schema                       │
└─────────────────────────────┬────────────────────────────────────┘
                              │  SELECT on emission_events
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ANALYSIS LAYER                             │
│  MirkwoodAnalyst: NL → schema-in-prompt Gemini → SQL → results   │
│  Read-only SQLite URI enforces write safety at engine level      │
│  CANNOT_ANSWER escape hatch for out-of-scope queries             │
└──────────────────────────────────────────────────────────────────┘
```

The full architectural reasoning — including why heavier stacks (RAG, vector store, agent frameworks) were rejected — is in [`architecture.md`](architecture.md).

---

## The Mathematics of Cross-Channel Correlation

### Device Fingerprint

Each adapter produces a stable `device_fingerprint` using a channel-appropriate normalization:

**MAC-based channels (BLE, WiFi, BT):**

$$f = \text{SHA-256}\!\left(\text{normalize}(\text{MAC})\right)$$

where $\text{normalize}(\text{MAC})$ strips separators and lowercases:

```
AA:BB:CC:DD:EE:FF  →  aabbccddeeff  →  SHA-256 → fingerprint
aa:bb:cc:dd:ee:ff  →  aabbccddeeff  →  SHA-256 → same fingerprint
```

This ensures a device observed by `rfparty` (BLE) and `wardriver_rev3` (WiFi) with the same hardware MAC produces an identical fingerprint across both rows.

**Radio-based channels (P25/EDACS):**

$$f = \text{SHA-256}(\texttt{"P25:}\langle\text{unit\_id}\rangle\texttt{:"} \| \texttt{"}\langle\text{talkgroup\_id}\rangle\texttt{"})$$

**SIP:**

$$f = \text{SHA-256}(\texttt{"SIP:}\langle\text{extension}\rangle\texttt{"})$$

**LTE (RNTI-based):**

$$f = \text{SHA-256}(\texttt{"LTE:}\langle\text{rnti}\rangle\texttt{:}\langle\text{cell\_id}\rangle\texttt{"})$$

### Spatiotemporal Join

Cross-channel correlation is a spatiotemporal join on `device_fingerprint` and `timestamp`:

$$\text{correlated\_pair} = \{(e_i, e_j) : f(e_i) = f(e_j) \;\land\; |t_i - t_j| < \Delta t \;\land\; i \neq j\}$$

In SQL:

```sql
SELECT a.channel_type   AS channel_a,
       b.channel_type   AS channel_b,
       a.primary_id     AS id_a,
       b.primary_id     AS id_b,
       a.device_fingerprint,
       ABS(strftime('%s', a.timestamp) - strftime('%s', b.timestamp)) AS dt_seconds
FROM   emission_events a
JOIN   emission_events b
  ON   a.device_fingerprint = b.device_fingerprint
 AND   a.channel_type       != b.channel_type
 AND   ABS(strftime('%s', a.timestamp) - strftime('%s', b.timestamp)) < 300
LIMIT  100;
```

A device appearing on two channels within a 5-minute window at the same location is a **co-presence hypothesis**, not an identity confirmation. The distinction matters under the false positive problem below.

### EDACS Talkgroup Metadata

P25/EDACS control channels broadcast trunking grants in the clear even when voice is encrypted. The 21-bit channel-grant word carries operational structure without decrypting a single syllable:

```
Bit [20:18]  LCID type
  0x01 = GROUP_GRANT       — active voice grant to a talkgroup
  0x05 = EMERGENCY         — emergency activation
  0x06 = AFFILIATION       — unit joining a talkgroup

Bit [17:11]  LCID (7 bits) — logical channel identifier
Bit [10:0]   Group/unit    — talkgroup or unit address (11 bits)
```

Grant rate per talkgroup over a sliding window is a proxy for operational tempo:

$$\lambda_g(t) = \frac{\text{grants}(g, [t-W, t])}{W}$$

where $W$ is the observation window width. Surge detection uses a z-score against a rolling baseline — the same formula used in SENTINEL-NODE's $T_d(t)$ term.

### The False Positive Problem

In high-density environments, devices co-locate by coincidence. The expected number of false correlation locks in a population of $N$ devices over observation window $W$ is:

$$\mathbb{E}[\text{false locks}] \approx \binom{N}{2} \cdot P(\text{same location} \mid \Delta t < W)$$

At a transit hub with $N = 500$ devices, a 5-minute window, and a coincidental co-location probability of $10^{-3}$, this yields roughly 125 spurious locks per window. The interface surfaces candidates for investigation under lawful process. It does not adjudicate them.

---

## Integrated Tools

| Tool | Adapter class | Channel | `channel_type` | `source_tool` |
|------|--------------|---------|----------------|---------------|
| [BearSentinel](https://github.com/GlomarGadaffi/BearSentinel) | `BearSentinelAdapter` | P25 / EDACS | `P25_TRUNK` | `BearSentinel` |
| [MeshNarc](https://github.com/GlomarGadaffi/MeshNarc) | `MeshNarcAdapter` | LoRa Mesh | `MESHTASTIC` | `MeshNarc` |
| [rfparty-xyz](https://github.com/rfparty-xyz/rfparty) | `RfpartyAdapter` | BLE | `BLE` | `rfparty` |
| [wardriver_rev3](https://github.com/GlomarGadaffi/wardriver_rev3) | `WardriverAdapter` | WiFi + BT | `WIFI` / `BT` | `wardriver_rev3` |
| [pocket-dial](https://github.com/GlomarGadaffi/pocket-dial) | `PocketDialAdapter` | SIP/VoIP | `SIP` | `pocket-dial` |
| [LTESniffer](https://github.com/SysSec-KAIST/LTESniffer) | `LTESnifferAdapter` | LTE control plane | `LTE` | `LTESniffer` |
| [Rayhunter](https://github.com/EFForg/rayhunter) | `RayhunterAdapter` | Rogue cell / IMSI catcher | `ROGUE_CELL` | `Rayhunter` |

---

## EmissionEvent Schema

All data normalizes to a single `EmissionEvent` (full definition in [`EmissionEvent_Schema.md`](EmissionEvent_Schema.md)):

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Unique event identifier |
| `timestamp` | datetime | UTC observation time |
| `latitude`, `longitude` | float | Observer position |
| `channel_type` | str | Protocol family (`P25_TRUNK`, `BLE`, `WIFI`, …) |
| `source_tool` | str | Originating tool name |
| `primary_id` | str | Main pseudonym for this channel |
| `secondary_ids` | list[str] | Secondary identifiers (service UUIDs, talkgroups, …) |
| `device_fingerprint` | str | SHA-256 cross-channel stable identifier |
| `metadata` | dict | Protocol-specific structured fields |
| `tags` | list[str] | Categorical labels |
| `enrichment` | dict | Post-processing additions (WiGLE, OUI vendor, AgencyDB) |

The schema is the methodology. Cross-channel correlation is a join on `device_fingerprint` + temporal proximity. Everything else is data.

---

## Usage

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
```

**Ingest data:**

```bash
# Directory watcher + TCP server on :8900
python -m adapters.pipeline --db mirkwood.db

# Add stdin reader (POSIX only)
python -m adapters.pipeline --db mirkwood.db --stdin

# Database statistics
python -m adapters.pipeline --stats --db mirkwood.db
```

**Send test events over TCP:**

```bash
echo '{"source_tool":"BearSentinel","payload":{"timestamp":"2026-06-04T20:00:00Z","lat":44.93,"lon":-93.27,"unit_id":12345,"talkgroup_id":20001,"grant_type":"grant","call_id":"call-1","system_type":"P25"}}' | nc 127.0.0.1 8900
```

**Query in natural language:**

```bash
export GEMINI_API_KEY="..."
python -m adapters.analyst_cli \
  "Find all BLE beacons co-located with a P25 talkgroup grant within 5 minutes" \
  --db mirkwood.db
```

The analyst generates a read-only `SELECT` (or `WITH ... SELECT` for CTEs), executes it on a read-only URI connection, and returns results with the generated SQL for audit. `CANNOT_ANSWER` is returned for queries outside the schema's scope.

**Run the test suite:**

```bash
python tests/test_adapters.py
```

All nine tests should pass: seven adapters, `DatabaseStore`, and `MirkwoodAnalyst` (mocked API).

---

## Repository Structure

```
Mirkwood/
├── adapters/
│   ├── base.py                 — GeoPoint, EmissionEvent, NormalizationAdapter protocol
│   ├── mirkwood_normalizer.py  — Adapter router
│   ├── database.py             — DatabaseStore (SQLite, 4 indexes, read-only URI mode)
│   ├── pipeline.py             — IngestionPipeline (async; dir watcher / TCP / stdin)
│   ├── analyst.py              — MirkwoodAnalyst (NL → SQL → results)
│   ├── analyst_cli.py          — Terminal interface
│   ├── bcd325p2.py             — BearSentinel adapter (P25 / EDACS)
│   ├── meshnarc.py             — MeshNarc adapter (LoRa Mesh)
│   ├── rfparty.py              — rfparty adapter (BLE)
│   ├── wardriver.py            — wardriver_rev3 adapter (WiFi + BT)
│   ├── pocket_dial.py          — pocket-dial adapter (SIP/VoIP)
│   ├── lte_sniffer.py          — LTESniffer adapter (LTE control plane)
│   └── rayhunter.py            — Rayhunter adapter (rogue cell / IMSI catcher)
├── tests/
│   └── test_adapters.py        — Full adapter + DB + analyst validation suite
├── DISCLAIMER.md               — Scope, false-positive statement, prohibited uses
├── EmissionEvent_Schema.md     — Unified schema definition
├── architecture.md             — Layer design and rationale
├── requirements.txt
└── README.md
```

---

## What Is Not Here

The capture layer — hardware BOM, firmware, RF containment configuration, and synthetic scenario generator — is not published and will not be. That is described in [`DISCLAIMER.md`](DISCLAIMER.md) and enforced by omission, not software policy.

The withheld components are the reproduction path. What is here demonstrates the methodology and the normalization pipeline. What is absent is what makes the methodology runnable against real hardware.

---

## Project Status

The ingestion pipeline, all seven adapters, the database layer, and the analyst interface are functional and test-passing. See the [wiki](https://github.com/GlomarGadaffi/Mirkwood/wiki) for detailed documentation on each adapter, the query interface, security considerations, and the SENTINEL-NODE defensive counterpart.

---

## See Also

- [`DISCLAIMER.md`](DISCLAIMER.md) — false positive problem stated plainly, bidirectionality, prohibited uses
- [`architecture.md`](architecture.md) — layer design decisions and rejected alternatives
- [`EmissionEvent_Schema.md`](EmissionEvent_Schema.md) — full schema with field descriptions
- [Mirkwood Wiki](https://github.com/GlomarGadaffi/Mirkwood/wiki) — adapter docs, query examples, security hardening, SENTINEL-NODE
- [sentinel-node](https://github.com/GlomarGadaffi/sentinel-node) — the defensive counterpart: what counter-surveillance systems look like and where they fail
