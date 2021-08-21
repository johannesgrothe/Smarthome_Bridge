from logging_interface import LoggingInterface

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic


class IdentifierEncodeError(Exception):
    def __init__(self, class_name: str):
        super().__init__(f"Cannot get identifier for gadget class '{class_name}'")


class GadgetEncodeError(Exception):
    def __init__(self, class_name: str, gadget_name):
        super().__init__(f"Cannot encode {class_name} '{gadget_name}'")


class ApiEncoder(LoggingInterface):
    def __init__(self):
        super().__init__()

    def encode_gadget(self, gadget: Gadget) -> dict:
        try:
            identifier = self._get_type_for_gadget(gadget)
        except IdentifierEncodeError as err:
            self._logger.error(err.args[0])
            raise GadgetEncodeError(gadget.__class__.__name__, gadget.get_name())

        characteristics_json = [self.encode_characteristic(x) for x in gadget.get_characteristics()]

        gadget_json = {"type": int(identifier),
                       "name": gadget.get_name(),
                       "characteristics": characteristics_json}

        return gadget_json

    @staticmethod
    def encode_characteristic(characteristic: Characteristic):
        return {"type": int(characteristic.get_type()),
                "min": characteristic.get_min(),
                "max": characteristic.get_max(),
                "steps": characteristic.get_steps(),
                "val": characteristic.get_step_value()}

    @staticmethod
    def _get_type_for_gadget(gadget: Gadget) -> GadgetIdentifier:
        switcher = {
            "AnyGadget": GadgetIdentifier.any_gadget,
            "FanWestinghouseIR": GadgetIdentifier.fan_westinghouse_ir,
            "LampNeopixelBasic": GadgetIdentifier.lamp_neopixel_basic
        }
        identifier = switcher.get(gadget.__class__.__name__, None)
        if identifier is None:
            raise IdentifierEncodeError(gadget.__class__.__name__)
        return identifier
