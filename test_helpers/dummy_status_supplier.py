from typing import Optional

from gadgets.gadget import Gadget
from smarthome_bridge.gadget_status_supplier import GadgetStatusSupplier


class DummyStatusSupplier(GadgetStatusSupplier):
    gadgets: list[Gadget]

    def __init__(self):
        super().__init__()
        self.gadgets = []

    def get_gadget(self, name: str) -> Optional[Gadget]:
        for gadget in self.gadgets:
            if gadget.get_name() == name:
                return gadget
        return None
