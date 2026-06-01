from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class RfpartyAdapter(NormalizationAdapter):
    channel_type = "BLE"
    source_tool = "rfparty"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        event = EmissionEvent(
            event_id=uuid4(),
            timestamp=raw['timestamp'],
            latitude=raw.get('lat'),
            longitude=raw.get('lon'),
            accuracy_m=raw.get('accuracy'),
            location_source="ble_scan",
            channel_type=self.channel_type,
            source_tool=self.source_tool,
            primary_id=str(raw.get('mac')) if raw.get('mac') is not None else None,
            secondary_ids=[str(s) for s in raw.get('service_uuids', [])] if raw.get('service_uuids') is not None else [],
            device_fingerprint=None,
            metadata={
                "mac": raw.get("mac"),
                "oui": raw.get("oui"),
                "name": raw.get("name"),
                "rssi": raw.get("rssi"),
                "service_uuids": raw.get("service_uuids")
            },
            observed_duration=None,
            session_id=None,
            tags=["beacon"],
            enrichment={}
        )
        return [event]

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Stable SHA-256 of cleaned MAC address to match cross-channel
        mac_clean = event.primary_id.replace(':', '').replace('-', '').lower().strip()
        return hashlib.sha256(mac_clean.encode('utf-8')).hexdigest()