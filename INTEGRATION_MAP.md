# Mirkwood Ingestion & Ecosystem Integration Map

This document establishes how the Mirkwood spatiotemporal correlation pipeline ingests, translates, and normalizes the data exhaust from all of **GlomarGadaffi's** capturing nodes and specialized network repositories.

Mirkwood acts as the **master fusion engine** for the ecosystem. While each individual project operates independently as a sensor, edge node, or signaling proxy, Mirkwood brings their telemetry into a single, cohesive database table (`emission_events`) to reveal cross-channel connections.

---

## Ecosystem Integration Tree

```text
GlomarGadaffi/ Emitters & Capture Nodes
├── BearSentinel (BCD325P2 telemetry) ──────> adapters/bcd325p2.py ──┐
├── MeshNarc (LoRa Meshtastic packet) ──────> adapters/meshnarc.py ───┤
├── rfparty-xyz (BLE Situational) ──────────> adapters/rfparty.py ────┤
├── wardriver_rev3 (WiFi + BT scans) ───────> adapters/wardriver.py ──┼─> [Mirkwood Normalizer Ingestion]
├── pocket-dial (SIP VoIP signaling) ───────> adapters/pocket_dial.py ┤
├── Rayhunter (Cell IMSI-Catcher) ──────────> adapters/rayhunter.py ──┤
├── LTESniffer (LTE Control Plane) ─────────> adapters/lte_sniffer.py ┘
│
├── SplunkUniden & p25logger ───────────────> Feeds BearSentinel
├── BC325P2-Spec ───────────────────────────> Defines BearSentinel schemas
├── CDRChat ────────────────────────────────> Feeds pocket-dial / CDR records
├── LoraWalk & AspenSniff ──────────────────> Feeds MeshNarc / Wardriver
└── i-am-the-CA-now- & shroud-speak ────────> Secures/encrypts VoIP & SIP signalling
```

---

## Repository Mapping & Normalization Schemas

### 1. BearSentinel & p25logger (Trunked Radio)
*   **Sensor Repositories:** [BearSentinel](https://github.com/GlomarGadaffi/BearSentinel), [p25logger](https://github.com/GlomarGadaffi/p25logger), [BC325P2-Spec](https://github.com/GlomarGadaffi/BC325P2-Spec)
*   **Telemetry Channel:** `P25_TRUNK` / `EDACS`
*   **Mirkwood Ingestion Module:** `adapters/bcd325p2.py`
*   **Data Structure Mapping:**
    *   `primary_id`: Handled as `unit_id` (radio terminal decimal) or `talkgroup_id`.
    *   `secondary_ids`: Handled as target `talkgroup_id`.
    *   `session_id`: Map `call_id` to correlate consecutive voice transmissions.
    *   `tags`: Transmitted as `"grant"` for operational channel leases, or `"telemetry"` for generic signals.
    *   **Fingerprint Logic:** Hashed using a stable SHA-256 profile of the radio Unit ID.

### 2. MeshNarc (LoRa Meshtastic SIGINT)
*   **Sensor Repository:** [MeshNarc](https://github.com/GlomarGadaffi/MeshNarc)
*   **Telemetry Channel:** `MESHTASTIC`
*   **Mirkwood Ingestion Module:** `adapters/meshnarc.py`
*   **Data Structure Mapping:**
    *   `primary_id`: LoRa node ID (e.g. `!2c3a5b6f`).
    *   `secondary_ids`: List of source and destination IDs (`from_id`, `to_id`).
    *   `location`: Direct spatial telemetry from GPS-enabled nodes.
    *   `tags`: Marked with `"mesh"` and `"position"` if coordinates are packed.
    *   **Fingerprint Logic:** Stable SHA-256 of the node's hardcoded hardware address.

### 3. rfparty-xyz (Bluetooth Low Energy)
*   **Sensor Repository:** [rfparty-xyz](https://github.com/GlomarGadaffi/rfparty-xyz)
*   **Telemetry Channel:** `BLE`
*   **Mirkwood Ingestion Module:** `adapters/rfparty.py`
*   **Data Structure Mapping:**
    *   `primary_id`: Bluetooth MAC Address.
    *   `secondary_ids`: Array of announced GATT Service UUIDs (reveals device brand/type).
    *   `tags`: Marked as `"beacon"`.
    *   **Fingerprint Logic:** Cleans the MAC address (removes colons, downcases) and hashes it to enable stable cross-channel matching (e.g., if a WiFi device matches the same MAC).

### 4. wardriver_rev3 (WiFi & Bluetooth Mapping)
*   **Sensor Repository:** [wardriver_rev3](https://github.com/GlomarGadaffi/wardriver_rev3), [LoraWalk](https://github.com/GlomarGadaffi/LoraWalk), [AspenSniff](https://github.com/GlomarGadaffi/AspenSniff)
*   **Telemetry Channel:** `WIFI` / `BT`
*   **Mirkwood Ingestion Module:** `adapters/wardriver.py`
*   **Data Structure Mapping:**
    *   `primary_id`: Access Point BSSID or Bluetooth MAC.
    *   `enrichment`: Maps to WiGLE historical geolocations (first seen, last seen, total observations).
    *   `tags`: Marked as `"wifi"` or `"bluetooth"`.
    *   **Fingerprint Logic:** Standardized MAC hashing that aligns perfectly with BLE scanners (like `rfparty`).

### 5. pocket-dial (VoIP/SIP Signaling Intercom)
*   **Sensor Repository:** [pocket-dial](https://github.com/GlomarGadaffi/pocket-dial), [CDRChat](https://github.com/GlomarGadaffi/CDRChat), [shroud-speak](https://github.com/GlomarGadaffi/shroud-speak)
*   **Telemetry Channel:** `SIP`
*   **Mirkwood Ingestion Module:** `adapters/pocket_dial.py`
*   **Data Structure Mapping:**
    *   `primary_id`: Phone extension or source SIP URI.
    *   `secondary_ids`: Destination contact URI.
    *   `session_id`: Call ID matching the SIP transaction dialog.
    *   `tags`: Marked with state (`"RINGING"`, `"BUSY"`, `"OK"`).
    *   **Fingerprint Logic:** Stable SHA-256 of phone extension, linking calling users.

### 6. Rayhunter (IMSI Catcher Detector)
*   **Sensor Repository:** Ingests cell-site simulators anomalies (from ported/community builds).
*   **Telemetry Channel:** `IMSI_CATCHER_DETECT`
*   **Mirkwood Ingestion Module:** `adapters/rayhunter.py`
*   **Data Structure Mapping:**
    *   `primary_id`: Cell Tower ID (PCI/EARFCN/TAC).
    *   `secondary_ids`: Trigger event name (e.g. `IMSI_REQUEST`, `DOWNGRADE_DETECTED`).
    *   `tags`: Marked with `"cellular"`, `"rogue"`, `"downgrade"`.
    *   **Fingerprint Logic:** Stable hash of Cell ID to track recurring suspect tower installations.

---

## The Correlation Advantage

By normalizing all these tools into Mirkwood's unified schema, you can perform queries that span across your entire hardware ecosystem:

1.  **Cross-Channel Spatiotemporal Join**: Locate where a specific Uniden `BearSentinel` Unit ID was keying at the exact millisecond a Meshtastic `MeshNarc` node broadcasted a message within 50 meters.
2.  **Hardware Address Fusion**: Correlate a WiFi access point detected by `wardriver_rev3` with a BLE tracking signature cataloged by `rfparty-xyz`.
3.  **Metadata Association**: Link SIP metadata from `pocket-dial`/`CDRChat` with cellular anomalies recorded by `Rayhunter`.
