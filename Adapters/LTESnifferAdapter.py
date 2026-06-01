class LTESnifferAdapter(NormalizationAdapter):
    channel_type = "LTE_SNIFFER"
    source_tool = "LTESniffer"

    def normalize(self, raw: Dict) -> List[EmissionEvent]:
        event = EmissionEvent(
            event_id=uuid4(),
            timestamp=raw['timestamp'],
            latitude=raw.get('lat'),
            longitude=raw.get('lon'),
            accuracy_m=30.0,
            location_source="rtlsdr_gps",
            channel_type=self.channel_type,
            source_tool=self.source_tool,
            primary_id=raw.get('rnti') or raw.get('cell_id'),
            secondary_ids=[raw.get('tmsi'), raw.get('imsi_fragment')],
            device_fingerprint=None,
            metadata=raw,
            observed_duration=None,
            session_id=None,
            tags=["cellular"],
            enrichment={}
        )
        return [event]