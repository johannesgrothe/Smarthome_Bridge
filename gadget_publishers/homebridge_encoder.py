from lib.logging_interface import LoggingInterface

from gadgets.gadget import Gadget
from system.gadget_definitions import CharacteristicIdentifier
from gadgets.fan import Fan
from gadgets.lamp import Lamp
from gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator

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
#
# homebridge/to/remove
# {
#     "name": "living_lamp",
# }


class GadgetEncodeError(Exception):
    def __init__(self, gadget: Gadget):
        super().__init__(f"Failed to decode {gadget.get_name()}/{gadget.__class__.__name__}")


class HomebridgeEncoder(LoggingInterface):

    def __init__(self):
        super().__init__()

    def encode_gadget(self, gadget: Gadget) -> dict:
        """
        Encodes a gadget for an 'add'-request to homebridge

        :param gadget: The gadget to generate the json for
        :return: Json-representation of the gadget
        :raises GadgetEncodeError: If gadget could not be encoded
        """
        if issubclass(gadget.__class__, Fan):
            return self._encode_fan(gadget)
        elif issubclass(gadget.__class__, Lamp):
            return self._encode_lamp(gadget)
        raise GadgetEncodeError(gadget)

    @staticmethod
    def _get_base_info(gadget: Gadget) -> dict:
        return {
            "name": gadget.get_name(),
            "service_name": gadget.get_name(),
        }

    def _encode_fan(self, gadget: Gadget) -> dict:
        out_dict = self._get_base_info(gadget)
        out_dict["service"] = "Fan"

        for characteristic_type in [CharacteristicIdentifier.status, CharacteristicIdentifier.fan_speed]:
            hb_name = HomebridgeCharacteristicTranslator.type_to_string(characteristic_type)
            out_dict[hb_name] = self._encode_characteristic(gadget, characteristic_type)
        return out_dict

    def _encode_lamp(self, gadget: Gadget) -> dict:
        out_dict = self._get_base_info(gadget)
        out_dict["service"] = "Lightbulb"

        for characteristic_type in [CharacteristicIdentifier.status,
                                    CharacteristicIdentifier.brightness,
                                    CharacteristicIdentifier.hue,
                                    CharacteristicIdentifier.saturation]:
            hb_name = HomebridgeCharacteristicTranslator.type_to_string(characteristic_type)
            out_dict[hb_name] = self._encode_characteristic(gadget, characteristic_type)
        return out_dict

    @staticmethod
    def _encode_characteristic(gadget: Gadget, characteristic_type: CharacteristicIdentifier) -> dict:
        gadget_characteristic = gadget.get_characteristic(characteristic_type)
        value_range = gadget_characteristic.get_max() - gadget_characteristic.get_min()
        min_step = value_range // gadget_characteristic.get_steps()
        return {"minValue": gadget_characteristic.get_min(),
                "maxValue": gadget_characteristic.get_max(),
                "minStep": min_step}
