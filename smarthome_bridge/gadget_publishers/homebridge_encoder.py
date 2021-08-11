from logging_interface import LoggingInterface

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadgets.fan import Fan
from smarthome_bridge.gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator

# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts

# homebridge/to/get
# {"name": "*"}
#
# homebridge/to/add
# {
#     "name": "living_lamp",
#     "service_name": "light",
#     "service": "Lightbulb",
#     "Brightness": "default"
# }


class GadgetEncodeError(Exception):
    def __init__(self, gadget: Gadget):
        super().__init__(f"Failed to decode {gadget.get_name()}/{gadget.get_type()}")


class HomebridgeEncoder(LoggingInterface):

    def __init__(self):
        super().__init__()

    def encode_gadget(self, gadget: Gadget) -> dict:
        if issubclass(gadget.__class__, Fan):
            return self._encode_fan(gadget)

    @staticmethod
    def _get_base_info(gadget: Gadget) -> dict:
        return {
            "name": gadget.get_name(),
            "service_name": gadget.get_name(),
        }

    def _encode_fan(self, gadget: Gadget) -> dict:
        out_dict = self._get_base_info(gadget)
        out_dict["service"] = "Fan"

        for characteristic_type in [CharacteristicIdentifier.status, Cha]:
            hb_name = HomebridgeCharacteristicTranslator.type_to_string(characteristic_type)
            out_dict[hb_name] = self._encode_characteristic(gadget, characteristic_type)
        return out_dict

    @staticmethod
    def _encode_characteristic(gadget: Gadget, characteristic_type: CharacteristicIdentifier) -> dict:
        gadget_characteristic = gadget.get_characteristic(characteristic_type)
        return {"minValue": gadget_characteristic.get_min(),
                "maxValue": gadget_characteristic.get_max(),
                "minStep": gadget_characteristic.get_steps()}
