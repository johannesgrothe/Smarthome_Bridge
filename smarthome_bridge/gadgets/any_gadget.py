from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier


class AnyGadget(Gadget):

    def __init__(self,
                 name: str,
                 g_type: GadgetIdentifier,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name,
                         g_type,
                         host_client,
                         characteristics)
