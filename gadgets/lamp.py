from gadgets.gadget import Gadget, GadgetIdentifier, Characteristic


class Lamp(Gadget):
    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name, host_client, characteristics)
