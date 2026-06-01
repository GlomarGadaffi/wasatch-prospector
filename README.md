# Mirkwood

**A synthetic research platform for demonstrating cross-channel pseudonymity collapse through passive RF observation.**

> "To see is to be bound."  
> Per-channel anonymity is deniable. The joint distribution is not.

---

## Purpose

Mirkwood is a **research instrument** that shows how multiple independent wireless channels — when observed together — can defeat pseudonymity without breaking any single protocol's encryption.

It fuses emissions from:
- Public safety trunked radio (P25/EDACS)
- LoRa mesh networks
- BLE/IoT devices
- WiFi & Bluetooth
- SIP/VoIP signaling
- LTE control plane
- Rogue cell detection

All **public artifacts are strictly synthetic**. No real captures are provided or reproducible.

## Architecture Overview

Mirkwood consists of three layers:

1. **Capture Layer** — Your existing tools (independent repos)
2. **Ingestion Layer** — Unified `EmissionEvent` normalization
3. **Analysis Layer** — Simple natural-language-to-SQL analyst with full schema-in-prompt

### Integrated Tools

| Tool                | Purpose                          | Channel                  | Status      |
|---------------------|----------------------------------|--------------------------|-------------|
| **BearSentinel**    | BCD325P2 trunked radio telemetry | P25 / EDACS              | Integrated  |
| **MeshNarc**        | Passive Meshtastic SIGINT        | LoRa Mesh                | Integrated  |
| **rfparty-xyz**     | BLE situational awareness        | Bluetooth Low Energy     | Integrated  |
| **wardriver_rev3**  | WiFi + BT wardriving             | 802.11 / BT              | Integrated  |
| **pocket-dial**     | Lightweight SIP PBX              | VoIP Signaling           | Integrated  |
| **LTESniffer**      | RTL-SDR LTE downlink             | LTE Control Plane        | Integrated  |
| **Rayhunter**       | EFF rogue cell / IMSI-catcher detector | Cellular Surveillance | Integrated  |

## Core Primitive

All data is normalized into a single `EmissionEvent` structure (see [`EmissionEvent_Schema.md`](EmissionEvent_Schema.md)).

Key fields include:
- `timestamp`, `location`, `channel_type`
- `primary_id` + `secondary_ids`
- `device_fingerprint` (cross-channel)
- `metadata` (protocol rich data)
- `tags`, `enrichment` (WiGLE, OUI, AgencyDB, etc.)

## Features

- Unified ingestion pipeline with per-tool adapters
- Spatiotemporal correlation engine
- Device tracking across channels
- WiGLE enrichment (BSSID history, fixed AP detection)
- Natural language analyst interface (schema-in-prompt + LLM)
- Synthetic scenario generator
- Strong focus on false-positive awareness and threat modeling

## Project Status

**Research Instrument** — Not a product.  
Primarily intended for:
- Red team / blue team awareness
- Accountability research
- Understanding modern surveillance dynamics
- Preparedness / SIGINT education

## Repository Structure

```text
├── adapters/                  # Normalization pipeline adapters
│   ├── __init__.py            # Clean exports for Mirkwood Normalizer package
│   ├── base.py                # Core interfaces (EmissionEvent, NormalizationAdapter)
│   ├── bcd325p2.py            # BearSentinel adapter (P25 / EDACS Trunked Radio)
│   ├── lte_sniffer.py         # LTESniffer adapter (LTE Control Plane)
│   ├── meshnarc.py            # MeshNarc adapter (LoRa Mesh/Meshtastic)
│   ├── mirkwood_normalizer.py # Main normalization router
│   ├── pocket_dial.py         # Pocket-dial adapter (VoIP SIP PBX)
│   ├── rayhunter.py           # Rayhunter adapter (Rogue cell detector / IMSI Catcher)
│   ├── rfparty.py             # rfparty adapter (BLE telemetry)
│   └── wardriver.py           # wardriver_rev3 adapter (WiFi + Bluetooth)
├── tests/                     # Validation suite
│   └── test_adapters.py       # Standalone test runner for normalization and fingerprinting
├── DISCLAIMER.md              # Project boundaries, false-positive stating, ethical considerations
├── EmissionEvent_Schema.md    # Unified DB schema definition
├── architecture.md            # In-depth architectural design decisions
├── mirkwood.png               # System architecture visual diagram
├── requirements.txt           # Package dependencies
└── README.md                  # Project overview and introduction
```
