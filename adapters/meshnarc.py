from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class MeshNarcAdapter(NormalizationAdapter):
    channel_type = "MESHTASTIC"
    source_tool = "MeshNarc"

    def normalize(self, raw_packet: Any) -> List[EmissionEvent]:
        event = EmissionEvent(
            event_id=uuid4(),
            timestamp=raw_packet['timestamp'],
            latitude=raw_packet.get('latitude'),
            longitude=raw_packet.get('longitude'),
            accuracy_m=raw_packet.get('accuracy'),
            location_source="meshtastic_gps",
            channel_type=self.channel_type,
            source_tool=self.source_tool,
            primary_id=str(raw_packet.get('node_id')) if raw_packet.get('node_id') is not None else None,
            secondary_ids=[str(raw_packet.get('from_id')) if raw_packet.get('from_id') is not None else None,
                           str(raw_packet.get('to_id')) if raw_packet.get('to_id') is not None else None],
            device_fingerprint=None,
            metadata={
                "node_id": raw_packet.get("node_id"),
                "long_name": raw_packet.get("long_name"),
                "short_name": raw_packet.get("short_name"),
                "hop_count": raw_packet.get("hop_count"),
                "rssi": raw_packet.get("rssi"),
                "snr": raw_packet.get("snr"),
                "payload_type": raw_packet.get("payload_type"),
                "text": raw_packet.get("text")
            },
            observed_duration=None,
            session_id=None,
            tags=["mesh"] + (["position"] if raw_packet.get('latitude') else []),
            enrichment={}
        )
        # Filter out None from secondary_ids
        event.secondary_ids = [sid for sid in event.secondary_ids if sid is not None]
        return [event]

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        if not event.primary_id:
            return None
        # Stable SHA-256 of primary identifier (Meshtastic node ID)
        return hashlib.sha256(f"MeshNarc:{event.primary_id}".encode('utf-8')).hexdigest()