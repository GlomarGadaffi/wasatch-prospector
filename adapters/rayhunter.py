from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class RayhunterAdapter(NormalizationAdapter):
    channel_type = "IMSI_CATCHER_DETECT"
    source_tool = "Rayhunter"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        records = raw if isinstance(raw, list) else [raw]
        events = []

        for r in records:
            event = EmissionEvent(
                event_id=uuid4(),
                timestamp=r['timestamp'],
                latitude=r.get('lat'),
                longitude=r.get('lon'),
                accuracy_m=r.get('accuracy', 10.0),
                location_source="rayhunter_gps",
                channel_type=self.channel_type,
                source_tool=self.source_tool,
                primary_id=str(r.get('cell_id')) if r.get('cell_id') is not None else None,
                secondary_ids=[str(r.get('suspicious_event'))] if r.get('suspicious_event') is not None else [],
                device_fingerprint=None,
                metadata={
                    "suspicious_event": r.get("suspicious_event"),
                    "cell_id": r.get("cell_id"),
                    "imsi_request": r.get("imsi_request"),
                    "downgrade_detected": r.get("downgrade_detected"),
                    "anomaly_score": r.get("anomaly_score")
                },
                observed_duration=None,
                session_id=None,
                tags=["cellular", "rogue"] + (["downgrade"] if r.get("downgrade_detected") else []),
                enrichment={}
            )
            events.append(event)
        return events

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Stable SHA-256 of primary identifier (Cell ID of IMSI catcher / cell)
        return hashlib.sha256(f"Rayhunter:{event.primary_id}".encode('utf-8')).hexdigest()
