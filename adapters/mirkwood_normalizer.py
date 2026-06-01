from typing import Dict, List, Any
from adapters.base import EmissionEvent
from adapters.bcd325p2 import BearSentinelAdapter
from adapters.meshnarc import MeshNarcAdapter
from adapters.rfparty import RfpartyAdapter
from adapters.wardriver import WardriverAdapter
from adapters.lte_sniffer import LTESnifferAdapter
from adapters.pocket_dial import PocketDialAdapter
from adapters.rayhunter import RayhunterAdapter


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
        if source_tool not in self.adapters:
            raise ValueError(f"No adapter registered for tool: {source_tool}")
        adapter = self.adapters[source_tool]
        events = adapter.normalize(raw_data)
        
        for event in events:
            event.device_fingerprint = adapter.generate_fingerprint(event)
            # TODO: Apply WiGLE enrichment, OUI lookup, etc.
        
        return events
