from gadgets.gadget import Gadget, Characteristic
from system.gadget_definitions import GadgetIdentifier


class Fan(Gadget):
    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name, host_client, characteristics)
