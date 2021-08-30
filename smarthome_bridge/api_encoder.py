from logging_interface import LoggingInterface

from smarthome_bridge.smarthomeclient import SmarthomeClient
from gadgets.gadget import Gadget, GadgetIdentifier
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

    def encode_client(self, client: SmarthomeClient) -> dict:
        """
        Serializes a clients data according to api specification

        :param client: The client to serialize
        :return: The serialized version of the client as dict
        """
        self._logger.debug(f"Serializing client '{client.get_name()}'")
        out_date = None
        if client.get_flash_date() is not None:
            out_date = client.get_flash_date().strftime("%Y-%m-%d %H:%M:%S")

        return {"name": client.get_name(),
                "created": client.get_created().strftime("%Y-%m-%d %H:%M:%S"),
                "last_connected": client.get_last_connected().strftime("%Y-%m-%d %H:%M:%S"),
                "runtime_id": client.get_runtime_id(),
                "is_active": client.is_active(),
                "boot_mode": client.get_boot_mode(),
                "sw_uploaded": out_date,
                "sw_commit": client.get_software_commit(),
                "sw_branch": client.get_software_branch(),
                "port_mapping": client.get_port_mapping()}

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
                "step_value": characteristic.get_step_value(),
                "true_value": characteristic.get_true_value(),
                "percentage_value": characteristic.get_percentage_value()}

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
