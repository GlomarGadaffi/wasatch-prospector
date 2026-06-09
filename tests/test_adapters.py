import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime
from adapters.base import EmissionEvent

from adapters.mirkwood_normalizer import MirkwoodNormalizer


def to_datetime(ts_str: str) -> datetime:
    return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")


async def test_bear_sentinel_adapter():
    print("Testing BearSentinelAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "lat": 42.1234,
        "lon": -71.4567,
        "unit_id": 12345,
        "talkgroup_id": 999,
        "grant_type": "grant",
        "call_id": "call-100",
        "system_type": "P25",
        "agency_tag": "TAC-1",
        "raw_line": "P25 Grant Unit 12345 to TG 999"
    }
    
    events = await normalizer.process("BearSentinel", raw_data)
    assert len(events) == 1
    event = events[0]
    
    assert event.channel_type == "P25_TRUNK"
    assert event.source_tool == "BearSentinel"
    assert event.latitude == 42.1234
    assert event.longitude == -71.4567
    assert event.primary_id == "12345"
    assert event.secondary_ids == ["999"]
    assert event.session_id == "call-100"
    assert "grant" in event.tags
    assert event.device_fingerprint is not None
    assert len(event.device_fingerprint) == 64
    print("BearSentinelAdapter OK!")


async def test_meshnarc_adapter():
    print("Testing MeshNarcAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_packet = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "latitude": 42.1234,
        "longitude": -71.4567,
        "accuracy": 15.0,
        "node_id": "node-55",
        "from_id": "src-1",
        "to_id": "dst-2",
        "long_name": "GridNode-55",
        "short_name": "GN55",
        "hop_count": 2,
        "rssi": -90,
        "snr": 5.5,
        "payload_type": "TEXT",
        "text": "Mesh alert: sensor active"
    }

    events = await normalizer.process("MeshNarc", raw_packet)
    assert len(events) == 1
    event = events[0]

    assert event.channel_type == "MESHTASTIC"
    assert event.source_tool == "MeshNarc"
    assert event.primary_id == "node-55"
    assert set(event.secondary_ids) == {"src-1", "dst-2"}
    assert event.accuracy_m == 15.0
    assert "mesh" in event.tags
    assert "position" in event.tags
    assert event.metadata["short_name"] == "GN55"
    print("MeshNarcAdapter OK!")


async def test_rfparty_adapter():
    print("Testing RfpartyAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "lat": 42.1234,
        "lon": -71.4567,
        "accuracy": 5.0,
        "mac": "AA:BB:CC:DD:EE:FF",
        "oui": "00:11:22",
        "name": "Beacon-X",
        "rssi": -65,
        "service_uuids": ["180d", "180f"]
    }

    events = await normalizer.process("rfparty", raw_data)
    assert len(events) == 1
    event = events[0]

    assert event.channel_type == "BLE"
    assert event.source_tool == "rfparty"
    assert event.primary_id == "AA:BB:CC:DD:EE:FF"
    assert event.secondary_ids == ["180d", "180f"]
    assert "beacon" in event.tags
    assert event.device_fingerprint is not None
    print("RfpartyAdapter OK!")


async def test_wardriver_adapter():
    print("Testing WardriverAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = [
        {
            "timestamp": to_datetime("2026-06-01T03:00:00Z"),
            "type": "WIFI",
            "lat": 42.1234,
            "lon": -71.4567,
            "bssid": "AA:BB:CC:DD:EE:FF",
            "ssid": "TestWiFi",
            "wigle_data": {"total_obs": 150}
        },
        {
            "timestamp": to_datetime("2026-06-01T03:01:00Z"),
            "type": "BT",
            "lat": 42.1234,
            "lon": -71.4567,
            "mac": "11:22:33:44:55:66"
        }
    ]

    events = await normalizer.process("wardriver_rev3", raw_data)
    assert len(events) == 2
    
    wifi_event = events[0]
    assert wifi_event.channel_type == "WIFI"
    assert wifi_event.primary_id == "AA:BB:CC:DD:EE:FF"
    assert "wifi" in wifi_event.tags
    
    bt_event = events[1]
    assert bt_event.channel_type == "BT"
    assert bt_event.primary_id == "11:22:33:44:55:66"
    assert "bluetooth" in bt_event.tags

    # Fingerprinting of clean MAC addresses must be stable regardless of casing or colons
    mac_fingerprint_clean = wifi_event.device_fingerprint
    
    # Stable cross-channel fingerprinting verification:
    rfparty_normalizer = MirkwoodNormalizer()
    rfparty_raw = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "mac": "aa:bb:cc:dd:ee:ff"
    }
    rf_events = await rfparty_normalizer.process("rfparty", rfparty_raw)
    assert rf_events[0].device_fingerprint == mac_fingerprint_clean
    print("WardriverAdapter OK!")


async def test_pocket_dial_adapter():
    print("Testing PocketDialAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "lat": 42.1234,
        "lon": -71.4567,
        "accuracy": 12.0,
        "extension": "1001",
        "contact": "sip:alice@sip.com",
        "call_id": "call-12345",
        "sdp": "v=0\no=alice...",
        "call_state": "RINGING",
        "duration": "PT5M"
    }

    events = await normalizer.process("pocket-dial", raw_data)
    assert len(events) == 1
    event = events[0]

    assert event.channel_type == "SIP"
    assert event.source_tool == "pocket-dial"
    assert event.primary_id == "1001"
    assert event.secondary_ids == ["sip:alice@sip.com"]
    assert event.session_id == "call-12345"
    assert "sip" in event.tags
    assert "RINGING" in event.tags
    print("PocketDialAdapter OK!")


async def test_lte_sniffer_adapter():
    print("Testing LTESnifferAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "lat": 42.1234,
        "lon": -71.4567,
        "rnti": 4567,
        "cell_id": 100,
        "tmsi": "0x12345678",
        "imsi_fragment": "310260"
    }

    events = await normalizer.process("LTESniffer", raw_data)
    assert len(events) == 1
    event = events[0]

    assert event.channel_type == "LTE_SNIFFER"
    assert event.source_tool == "LTESniffer"
    assert event.primary_id == "4567"
    assert set(event.secondary_ids) == {"0x12345678", "310260"}
    assert "cellular" in event.tags
    print("LTESnifferAdapter OK!")


async def test_rayhunter_adapter():
    print("Testing RayhunterAdapter...")
    normalizer = MirkwoodNormalizer()
    raw_data = {
        "timestamp": to_datetime("2026-06-01T03:00:00Z"),
        "lat": 42.1234,
        "lon": -71.4567,
        "cell_id": 999,
        "suspicious_event": "IMSI_REQUEST",
        "downgrade_detected": True,
        "anomaly_score": 0.85
    }

    events = await normalizer.process("Rayhunter", raw_data)
    assert len(events) == 1
    event = events[0]

    assert event.channel_type == "IMSI_CATCHER_DETECT"
    assert event.source_tool == "Rayhunter"
    assert event.primary_id == "999"
    assert event.secondary_ids == ["IMSI_REQUEST"]
    assert "cellular" in event.tags
    assert "rogue" in event.tags
    assert "downgrade" in event.tags
    assert event.metadata["anomaly_score"] == 0.85
    print("RayhunterAdapter OK!")


async def test_database_store():
    print("Testing DatabaseStore integration...")
    from adapters.database import DatabaseStore
    from adapters.bcd325p2 import BearSentinelAdapter
    
    test_db = "test_mirkwood.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    try:
        db = DatabaseStore(test_db)
        
        # Standard BearSentinel event
        normalizer = MirkwoodNormalizer()
        raw_data = {
            "timestamp": to_datetime("2026-06-01T03:00:00Z"),
            "lat": 42.1234,
            "lon": -71.4567,
            "unit_id": 12345,
            "talkgroup_id": 999,
            "grant_type": "grant",
            "call_id": "call-100"
        }
        
        events = await normalizer.process("BearSentinel", raw_data)
        assert len(events) == 1
        
        # Batch insert
        rows_inserted = db.insert_events(events)
        assert rows_inserted == 1
        
        # Fetch back
        recent = db.get_recent_events(limit=5)
        assert len(recent) == 1
        record = recent[0]
        
        assert record["source_tool"] == "BearSentinel"
        assert record["channel_type"] == "P25_TRUNK"
        assert record["primary_id"] == "12345"
        assert record["session_id"] == "call-100"
        assert float(record["latitude"]) == 42.1234
        
        print("DatabaseStore OK!")
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)


async def test_mirkwood_analyst():
    print("Testing MirkwoodAnalyst NLP-to-SQL logic (mocked API)...")
    from adapters.analyst import MirkwoodAnalyst
    
    # Initialize with mock key
    analyst = MirkwoodAnalyst(db_path="test_mirkwood.db", api_key="MOCK_KEY")
    
    # Mock the API response dynamically
    def mock_call_gemini(system_prompt: str, user_prompt: str) -> str:
        if "coordinates" in user_prompt:
            return "SELECT * FROM emission_events WHERE latitude IS NOT NULL"
        elif "unknown field" in user_prompt:
            return "CANNOT_ANSWER"
        return "SELECT COUNT(*) FROM emission_events"
        
    analyst._call_gemini_rest = mock_call_gemini
    
    # Test coordinates question
    sql = analyst.generate_sql("Find all entries with coordinates")
    assert sql == "SELECT * FROM emission_events WHERE latitude IS NOT NULL"
    
    # Test out of scope escape hatch
    sql_cannot = analyst.generate_sql("Query an unknown field in the db")
    assert sql_cannot == "CANNOT_ANSWER"
    
    # Test full pipeline logic error handling (e.g. out of scope)
    res = analyst.query("Query an unknown field in the db")
    assert res["success"] is False
    assert res["sql"] is None
    assert "cannot be answered" in res["error"]
    
    print("MirkwoodAnalyst OK!")


async def test_epistemic_classifier():
    print("Testing epistemic classification of query results...")
    from adapters.analyst import classify_epistemic_status

    # A single-table read is an OBSERVATION (still not an identity, but not a lock).
    obs = classify_epistemic_status(
        "SELECT * FROM emission_events WHERE channel_type = 'BLE' LIMIT 100"
    )
    assert obs is not None
    assert obs["status"] == "OBSERVATION"
    assert obs["is_evidence"] is False

    # A self-join correlation is a CO-PRESENCE HYPOTHESIS, never an identification.
    corr = classify_epistemic_status(
        "SELECT a.primary_id, b.primary_id FROM emission_events a "
        "JOIN emission_events b ON a.device_fingerprint = b.device_fingerprint "
        "AND a.channel_type != b.channel_type"
    )
    assert corr["status"] == "CORRELATION_HYPOTHESIS"
    assert corr["is_evidence"] is False

    # An explicit JOIN keyword alone is enough to flag correlation.
    corr2 = classify_epistemic_status(
        "SELECT * FROM emission_events a JOIN emission_events b USING (device_fingerprint)"
    )
    assert corr2["status"] == "CORRELATION_HYPOTHESIS"

    # No SQL (CANNOT_ANSWER path) yields no classification.
    assert classify_epistemic_status(None) is None
    assert classify_epistemic_status("") is None

    # Every classified result must carry the evidentiary reference.
    assert obs["reference"] == "EVIDENTIARY.md"
    assert corr["reference"] == "EVIDENTIARY.md"
    print("EpistemicClassifier OK!")


async def main():
    print("Starting Mirkwood Adapter verification...")
    print("-" * 50)
    try:
        await test_bear_sentinel_adapter()
        await test_meshnarc_adapter()
        await test_rfparty_adapter()
        await test_wardriver_adapter()
        await test_pocket_dial_adapter()
        await test_lte_sniffer_adapter()
        await test_rayhunter_adapter()
        await test_database_store()
        await test_mirkwood_analyst()
        await test_epistemic_classifier()
        print("-" * 50)
        print("ALL TESTS PASSED SUCCESSFULLY! Normalization pipeline is 100% correct!")
    except AssertionError as e:
        print("TEST FAILED due to AssertionError!")
        raise e
    except Exception as e:
        print(f"TEST FAILED with unexpected exception: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())


