from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class BearSentinelAdapter(NormalizationAdapter):
    channel_type = "P25_TRUNK"   # or "EDACS" depending on system
    source_tool = "BearSentinel"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        records = raw if isinstance(raw, list) else [raw]
        events = []
        for r in records:
            event = EmissionEvent(
                event_id=uuid4(),
                timestamp=r['timestamp'],
                latitude=r.get('lat'),
                longitude=r.get('lon'),
                accuracy_m=15.0,
                location_source="bcd325p2_gps",
                channel_type=self.channel_type,
                source_tool=self.source_tool,
                primary_id=str(r.get('unit_id')) if r.get('unit_id') is not None else (str(r.get('talkgroup_id')) if r.get('talkgroup_id') is not None else None),
                secondary_ids=[str(r.get('talkgroup_id'))] if r.get('talkgroup_id') is not None else [],
                device_fingerprint=None,
                metadata={
                    "grant_type": r.get("grant_type"),
                    "unit_id": r.get("unit_id"),
                    "talkgroup_id": r.get("talkgroup_id"),
                    "patch_id": r.get("patch_id"),
                    "lcn": r.get("lcn"),
                    "system_type": r.get("system_type"),
                    "agency_tag": r.get("agency_tag"),
                    "raw_line": r.get("raw_line")
                },
                observed_duration=None,
                session_id=str(r.get("call_id")) if r.get("call_id") is not None else None,
                tags=["grant"] if r.get("grant_type") else ["telemetry"],
                enrichment={}
            )
            events.append(event)
        return events

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Stable SHA-256 of primary identifier
        return hashlib.sha256(f"BearSentinel:{event.primary_id}".encode('utf-8')).hexdigest()
