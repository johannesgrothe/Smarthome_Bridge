from typing import Optional

from gadgets.remote.i_remote_gadget import IRemoteGadget
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier


class DummyStatusSupplier(GadgetStatusSupplier):
    gadgets: list[IRemoteGadget]

    def __init__(self):
        super().__init__()
        self.gadgets = []

    def get_gadget(self, name: str) -> Optional[IRemoteGadget]:
        for gadget in self.gadgets:
            if gadget.get_name() == name:
                return gadget
        return None
