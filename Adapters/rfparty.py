class RfpartyAdapter(NormalizationAdapter):
    channel_type = "BLE"
    source_tool = "rfparty"

    def normalize(self, raw: Dict) -> List[EmissionEvent]:
        event = EmissionEvent(
            event_id=uuid4(),
            timestamp=raw['timestamp'],
            latitude=raw.get('lat'),
            longitude=raw.get('lon'),
            accuracy_m=raw.get('accuracy'),
            location_source="ble_scan",
            channel_type=self.channel_type,
            source_tool=self.source_tool,
            primary_id=raw.get('mac'),
            secondary_ids=raw.get('service_uuids', []),
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