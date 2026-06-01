class MirkwoodNormalizer:
    def __init__(self):
        self.adapters = {
            "BearSentinel": BearSentinelAdapter(),
            "MeshNarc": MeshNarcAdapter(),
            "rfparty": RfpartyAdapter(),
            "wardriver_rev3": WardriverAdapter(),
            "pocket-dial": PocketDialAdapter(),
            "LTESniffer": LTESnifferAdapter(),
            "Rayhunter": RayhunterAdapter(),
        }

    async def process(self, source_tool: str, raw_data: Any) -> List[EmissionEvent]:
        adapter = self.adapters[source_tool]
        events = adapter.normalize(raw_data)
        
        for event in events:
            event.device_fingerprint = adapter.generate_fingerprint(event)
            # TODO: Apply WiGLE enrichment, OUI lookup, etc.
        
        return events