from smarthome_bridge.gadgets.lamp import Lamp, Characteristic, GadgetIdentifier


class LampNeopixelBasic(Lamp):
    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name,
                         GadgetIdentifier.fan_westinghouse_ir,
                         host_client,
                         characteristics)
