from gadgets.gadget import Gadget
from system.gadget_definitions import GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic


class AnyGadget(Gadget):

    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name,
                         host_client,
                         characteristics)
