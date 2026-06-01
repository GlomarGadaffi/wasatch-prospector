class WardriverAdapter(NormalizationAdapter):
    channel_type = "WIFI"          # Can also produce BT events
    source_tool = "wardriver_rev3"

    def normalize(self, raw: Dict | List) -> List[EmissionEvent]:
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
                primary_id=r.get('bssid') or r.get('mac'),
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