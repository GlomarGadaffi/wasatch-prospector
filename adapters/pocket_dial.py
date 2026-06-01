from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class PocketDialAdapter(NormalizationAdapter):
    channel_type = "SIP"
    source_tool = "pocket-dial"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        records = raw if isinstance(raw, list) else [raw]
        events = []

        for r in records:
            event = EmissionEvent(
                event_id=uuid4(),
                timestamp=r['timestamp'],
                latitude=r.get('lat'),
                longitude=r.get('lon'),
                accuracy_m=r.get('accuracy', 50.0),
                location_source="sip_server_location",
                channel_type=self.channel_type,
                source_tool=self.source_tool,
                primary_id=str(r.get('extension')) if r.get('extension') is not None else str(r.get('contact')) if r.get('contact') is not None else None,
                secondary_ids=[str(r.get('contact'))] if r.get('contact') is not None and r.get('extension') is not None else [],
                device_fingerprint=None,
                metadata={
                    "extension": r.get("extension"),
                    "call_id": r.get("call_id"),
                    "contact": r.get("contact"),
                    "sdp": r.get("sdp"),
                    "call_state": r.get("call_state")
                },
                observed_duration=str(r.get("duration")) if r.get("duration") is not None else None,
                session_id=str(r.get("call_id")) if r.get("call_id") is not None else None,
                tags=["sip", "voip"] + ([str(r.get("call_state"))] if r.get("call_state") else []),
                enrichment={}
            )
            events.append(event)
        return events

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Stable SHA-256 of SIP extension / identifier
        return hashlib.sha256(f"pocket-dial:{event.primary_id}".encode('utf-8')).hexdigest()
