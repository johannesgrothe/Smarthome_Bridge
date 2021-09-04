from logging_interface import LoggingInterface
from datetime import datetime

from smarthome_bridge.smarthomeclient import SmarthomeClient
from gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.bridge_information_container import BridgeInformationContainer


class IdentifierEncodeError(Exception):
    def __init__(self, class_name: str):
        super().__init__(f"Cannot get identifier for gadget class '{class_name}'")


class GadgetEncodeError(Exception):
    def __init__(self, class_name: str, gadget_name):
        super().__init__(f"Cannot encode {class_name} '{gadget_name}'")


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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
        if client.get_sw_flash_time() is not None:
            out_date = client.get_sw_flash_time().strftime(DATETIME_FORMAT)

        return {"name": client.get_name(),
                "created": client.get_created().strftime(DATETIME_FORMAT),
                "last_connected": client.get_last_connected().strftime(DATETIME_FORMAT),
                "runtime_id": client.get_runtime_id(),
                "is_active": client.is_active(),
                "boot_mode": client.get_boot_mode(),
                "sw_uploaded": out_date,
                "sw_commit": client.get_sw_commit(),
                "sw_branch": client.get_sw_branch(),
                "port_mapping": client.get_port_mapping()}

    def encode_gadget(self, gadget: Gadget) -> dict:
        """
        Serializes a gadget according to api specification

        :param gadget: The gadget to serialize
        :return: The serialized version of the gadget as dict
        :raises GadgetEncodeError: If anything goes wrong during the serialization process
        """
        try:
            identifier = self.encode_gadget_identifier(gadget)
        except IdentifierEncodeError as err:
            self._logger.error(err.args[0])
            raise GadgetEncodeError(gadget.__class__.__name__, gadget.get_name())

        characteristics_json = [self.encode_characteristic(x) for x in gadget.get_characteristics()]

        gadget_json = {"type": int(identifier),
                       "name": gadget.get_name(),
                       "characteristics": characteristics_json}

        return gadget_json

    @staticmethod
    def encode_gadget_identifier(gadget: Gadget) -> GadgetIdentifier:
        """
        Gets a gadget identifier for the class of the passed gadget

        :param gadget: The gadget to get the identifier for
        :return: The gadget identifier
        :raises IdentifierEncodeError: If no Identifier for the gadget can be found
        """
        switcher = {
            "AnyGadget": GadgetIdentifier.any_gadget,
            "FanWestinghouseIR": GadgetIdentifier.fan_westinghouse_ir,
            "LampNeopixelBasic": GadgetIdentifier.lamp_neopixel_basic
        }
        identifier = switcher.get(gadget.__class__.__name__, None)
        if identifier is None:
            raise IdentifierEncodeError(gadget.__class__.__name__)
        return identifier

    @staticmethod
    def encode_characteristic(characteristic: Characteristic) -> dict:
        """
        Serializes a characteristic according to api specification

        :param characteristic: The characteristic to serialize
        :return: The serialized version of the characteristic as dict
        """
        return {"type": int(characteristic.get_type()),
                "min": characteristic.get_min(),
                "max": characteristic.get_max(),
                "steps": characteristic.get_steps(),
                "step_value": characteristic.get_step_value(),
                "true_value": characteristic.get_true_value(),
                "percentage_value": characteristic.get_percentage_value()}

    @staticmethod
    def encode_bridge_info(bridge_info: BridgeInformationContainer) -> dict:
        """
        Serializes bridge information according to api specification

        :param bridge_info: Container for the bridge information
        :return:
        """
        return {"bridge_name": bridge_info.name,
                "software_commit": bridge_info.git_commit,
                "software_branch": bridge_info.git_branch,
                "running_since": datetime.strftime(bridge_info.running_since, DATETIME_FORMAT),
                "platformio_version": None,
                "git_version": None,
                "python_version": None,
                "pipenv_version": None}

    def encode_all_gadgets_info(self, gadget_info: list[Gadget]) -> dict:
        gadget_data = []
        for gadget in gadget_info:
            try:
                gadget_data.append(self.encode_gadget(gadget))
            except GadgetEncodeError:
                self._logger.error(f"Failed to encode gadget '{gadget.get_name()}'")
        return {"gadgets": gadget_data}

    def encode_all_clients_info(self, client_info: list[SmarthomeClient]) -> dict:
        client_data = []
        for client in client_info:
            try:
                client_data.append(self.encode_client(client))
            except GadgetEncodeError:
                self._logger.error(f"Failed to encode client '{client.get_name()}'")
        return {"clients": client_data}
