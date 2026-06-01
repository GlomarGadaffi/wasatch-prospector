from typing import Dict, List, Any, Optional
from uuid import uuid4
import hashlib
from adapters.base import NormalizationAdapter, EmissionEvent


class LTESnifferAdapter(NormalizationAdapter):
    channel_type = "LTE_SNIFFER"
    source_tool = "LTESniffer"

    def normalize(self, raw: Any) -> List[EmissionEvent]:
        event = EmissionEvent(
            event_id=uuid4(),
            timestamp=raw['timestamp'],
            latitude=raw.get('lat'),
            longitude=raw.get('lon'),
            accuracy_m=30.0,
            location_source="rtlsdr_gps",
            channel_type=self.channel_type,
            source_tool=self.source_tool,
            primary_id=str(raw.get('rnti')) if raw.get('rnti') is not None else (str(raw.get('cell_id')) if raw.get('cell_id') is not None else None),
            secondary_ids=[str(raw.get('tmsi')) if raw.get('tmsi') is not None else None,
                           str(raw.get('imsi_fragment')) if raw.get('imsi_fragment') is not None else None],
            device_fingerprint=None,
            metadata=raw,
            observed_duration=None,
            session_id=None,
            tags=["cellular"],
            enrichment={}
        )
        event.secondary_ids = [sid for sid in event.secondary_ids if sid is not None]
        return [event]

    def generate_fingerprint(self, event: EmissionEvent) -> Optional[str]:
        # For LTE, TMSI is temporary, RNTI is cell specific.
        # If we have an IMSI fragment or TMSI, hash them. Otherwise primary_id.
        if event.metadata.get('imsi_fragment'):
            return hashlib.sha256(f"imsi:{event.metadata.get('imsi_fragment')}".encode('utf-8')).hexdigest()
        if event.metadata.get('tmsi'):
            return hashlib.sha256(f"tmsi:{event.metadata.get('tmsi')}".encode('utf-8')).hexdigest()
        if not event.primary_id:
            return None
        return hashlib.sha256(f"LTESniffer:{event.primary_id}".encode('utf-8')).hexdigest()
