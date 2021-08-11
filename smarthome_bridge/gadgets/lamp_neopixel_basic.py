from smarthome_bridge.gadgets.lamp import Lamp, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic


class LampNeopixelBasic(Lamp):
    def __init__(self,
                 name: str,
                 host_client: str,
                 status: Characteristic,
                 brightness: Characteristic,
                 hue: Characteristic):
        super().__init__(name,
                         GadgetIdentifier.fan_westinghouse_ir,
                         host_client,
                         [status, brightness, hue])
