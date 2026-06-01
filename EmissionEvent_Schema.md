{
  "project": "Mirkwood",
  "version": "0.1",
  "description": "Unified EmissionEvent schema integrating all GlomarGadaffi repos for cross-channel RF fusion and correlation",
  "core_table": "emission_events",
  "schema": {
    "table_name": "emission_events",
    "columns": [
      {
        "name": "event_id",
        "type": "UUID",
        "primary_key": true,
        "default": "gen_random_uuid()",
        "description": "Unique event identifier"
      },
      {
        "name": "timestamp",
        "type": "TIMESTAMPTZ",
        "required": true,
        "description": "Event occurrence time (UTC)"
      },
      {
        "name": "ingest_timestamp",
        "type": "TIMESTAMPTZ",
        "default": "NOW()",
        "description": "When the event was ingested"
      },
      {
        "name": "latitude",
        "type": "DOUBLE PRECISION",
        "description": "Latitude in decimal degrees"
      },
      {
        "name": "longitude",
        "type": "DOUBLE PRECISION",
        "description": "Longitude in decimal degrees"
      },
      {
        "name": "accuracy_m",
        "type": "REAL",
        "description": "Location accuracy in meters"
      },
      {
        "name": "location_source",
        "type": "TEXT",
        "description": "Source of location data (GPS, meshtastic, wardriver, etc.)"
      },
      {
        "name": "geohash",
        "type": "TEXT",
        "description": "Geohash for fast spatial grouping"
      },
      {
        "name": "channel_type",
        "type": "TEXT",
        "required": true,
        "enum": [
          "P25_TRUNK", "EDACS", "MESHTASTIC", "BLE", "WIFI", "BT",
          "SIP", "LTE_CELL", "LTE_SNIFFER", "IMSI_CATCHER_DETECT", "OTHER"
        ]
      },
      {
        "name": "source_tool",
        "type": "TEXT",
        "required": true,
        "enum": [
          "BearSentinel", "MeshNarc", "rfparty", "wardriver_rev3",
          "pocket-dial", "LTESniffer", "Rayhunter"
        ]
      },
      {
        "name": "primary_id",
        "type": "TEXT",
        "description": "Main identifier (UnitID, TGID, BLE MAC, BSSID, Mesh Node ID, SIP Extension, etc.)"
      },
      {
        "name": "secondary_ids",
        "type": "TEXT[]",
        "description": "Array of related identifiers"
      },
      {
        "name": "device_fingerprint",
        "type": "TEXT",
        "description": "Stable cross-channel device/person identifier"
      },
      {
        "name": "metadata",
        "type": "JSONB",
        "required": true,
        "default": "{}",
        "description": "Protocol-specific rich data"
      },
      {
        "name": "observed_duration",
        "type": "INTERVAL",
        "description": "Duration of the observed activity"
      },
      {
        "name": "session_id",
        "type": "TEXT",
        "description": "Correlated session (call, conversation, movement track)"
      },
      {
        "name": "tags",
        "type": "TEXT[]",
        "description": "Semantic tags (grant, beacon, rogue, tactical, etc.)"
      },
      {
        "name": "enrichment",
        "type": "JSONB",
        "default": "{}",
        "description": "External enrichment (WiGLE, OUI, agency, etc.)"
      }
    ]
  },

  "recommended_indexes": [
    "timestamp DESC",
    "(channel_type, timestamp)",
    "(primary_id, timestamp)",
    "device_fingerprint",
    "location GEOGRAPHY",
    "geohash",
    "tags GIN",
    "(source_tool, timestamp)"
  ],

  "materialized_views": {
    "mv_device_tracks": "Tracks per device_fingerprint with first/last seen and geometry",
    "mv_proximity_pairs": "Events within 500m and 5 minutes of each other",
    "mv_high_activity_zones": "Hotspots by channel and time window"
  },

  "channel_metadata_schemas": {
    "BearSentinel": {
      "fields": ["grant_type", "unit_id", "talkgroup_id", "patch_id", "lcn", "system_id", "agency_tag", "raw_line"]
    },
    "MeshNarc": {
      "fields": ["node_id", "long_name", "short_name", "hop_count", "rssi", "snr", "payload_type", "text", "from_id", "to_id", "position"]
    },
    "rfparty": {
      "fields": ["mac", "service_uuids", "oui", "rssi", "manufacturer_data", "name"]
    },
    "wardriver_rev3": {
      "fields": ["bssid", "ssid", "encryption", "channel", "rssi", "wigle_first_seen", "wigle_last_seen", "wigle_total_obs"]
    },
    "pocket-dial": {
      "fields": ["extension", "call_id", "contact", "sdp", "call_state"]
    },
    "LTESniffer": {
      "fields": ["pci", "earfcn", "rnti", "tmsi", "imsi_fragment", "dci"]
    },
    "Rayhunter": {
      "fields": ["suspicious_event", "cell_id", "imsi_request", "downgrade_detected", "anomaly_score"]
    }
  },

  "correlation_primitives": [
    "spatiotemporal_window",
    "device_fingerprint",
    "logical_track",
    "co_occurrence_score",
    "correlation_lock",
    "suspicion_score"
  ],

  "enrichment_sources": {
    "wigle": ["first_seen", "last_seen", "total_observations", "encryption", "best_location"],
    "oui": ["manufacturer"],
    "agencydb": ["agency_name"]
  },

  "operational_primitives": {
    "edge_node": "Integrated hardware unit (ESP32 + BCD325P2 + RTL-SDR + Rayhunter)",
    "dead_drop": "Passive MeshNarc nodes with cellular backhaul",
    "containment": "Synthetic-only for public, air-gapped for real captures",
    "ingestion": "Normalization Service with per-tool adapters"
  },

  "analyst_layer": {
    "method": "schema-in-prompt + LLM → SQL",
    "sentinel": "CANNOT_ANSWER",
    "constraints": "Read-only, full schema context on every query"
  }
}
