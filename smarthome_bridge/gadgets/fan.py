from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic


class Fan(Gadget):
    def __init__(self,
                 name: str,
                 g_type: GadgetIdentifier,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name, g_type, host_client, characteristics)
