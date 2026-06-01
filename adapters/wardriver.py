from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class WardriverAdapter(NormalizationAdapter):
    channel_type = "WIFI"          # Can also produce BT events
    source_tool = "wardriver_rev3"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        records = raw if isinstance(raw, list) else [raw]
        events = []

        for r in records:
            ct = "BT" if r.get('type') == 'BT' else "WIFI"
            event = EmissionEvent(
                event_id=uuid4(),
                timestamp=r['timestamp'],
                latitude=r.get('lat'),
                longitude=r.get('lon'),
                accuracy_m=10.0,
                location_source="wardriver_gps",
                channel_type=ct,
                source_tool=self.source_tool,
                primary_id=str(r.get('bssid')) if r.get('bssid') is not None else (str(r.get('mac')) if r.get('mac') is not None else None),
                secondary_ids=[],
                device_fingerprint=None,
                metadata=r,   # Store full record
                observed_duration=None,
                session_id=None,
                tags=["wifi"] if ct == "WIFI" else ["bluetooth"],
                enrichment={"wigle": r.get("wigle_data")}
            )
            events.append(event)
        return events

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Standard stable SHA-256 of primary identifier (MAC address / BSSID)
        # Normalizing to lowercase with colons removed (if any) to ensure cross-channel correlation
        mac_clean = event.primary_id.replace(':', '').replace('-', '').lower().strip()
        return hashlib.sha256(mac_clean.encode('utf-8')).hexdigest()
