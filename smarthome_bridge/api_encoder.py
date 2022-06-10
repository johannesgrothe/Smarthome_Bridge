from typing import Tuple, Type

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from lib.logging_interface import ILogging
from datetime import datetime

from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.local_gadget import LocalGadget
from smarthome_bridge.api_coders.gadgets.denon_receiver_encoder import DenonReceiverEncoder
from smarthome_bridge.client import Client
from gadgets.remote.remote_gadget import RemoteGadget, Gadget
from system.gadget_definitions import GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.bridge_information_container import BridgeInformationContainer


class IdentifierEncodeError(Exception):
    def __init__(self, class_name: str):
        super().__init__(f"Cannot get identifier for gadget class '{class_name}'")


class GadgetEncodeError(Exception):
    def __init__(self, class_name: str, gadget_name: str, reason: str = "unknown"):
        super().__init__(f"Cannot encode {class_name} '{gadget_name}' because: {reason}")


class GadgetPublisherEncodeError(Exception):
    def __init__(self, class_name: str):
        super().__init__(f"Cannot encode {class_name}")


_gadget_publisher_name_mapping: dict[Type[GadgetPublisher], str] = {
    GadgetPublisherHomekit: "homekit"
}

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ApiEncoder(ILogging):
    def __init__(self):
        super().__init__()

    @classmethod
    def encode_client(cls, client: Client) -> dict:
        """
        Serializes a clients data according to api specification

        :param client: The client to serialize
        :return: The serialized version of the client as dict
        """
        cls._get_logger().debug(f"Serializing client '{client.get_name()}'")
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
                "port_mapping": client.get_port_mapping(),
                "api_version": str(client.get_api_version())}

    @classmethod
    def encode_gadget(cls, gadget: Gadget) -> dict:
        """
        Serializes a gadget according to api specification

        :param gadget: The gadget to serialize
        :return: The serialized version of the gadget as dict
        :raises GadgetEncodeError: If anything goes wrong during the serialization process
        """

        if isinstance(gadget, RemoteGadget):
            return self._encode_remote_gadget(gadget)
        elif isinstance(gadget, LocalGadget):
            return self._encode_local_gadget(gadget)
        raise GadgetEncodeError(gadget.__class__.__name__, gadget.get_name(), f"Gadget has unsupported type")

    def _encode_local_gadget(self, gadget: LocalGadget) -> dict:
        if isinstance(gadget, DenonRemoteControlGadget):
            return DenonReceiverEncoder.encode(gadget)
        raise GadgetEncodeError(gadget.__class__.__name__, gadget.id, f"LocalGadget has unsupported type")

    def _encode_remote_gadget(self, gadget: RemoteGadget) -> dict:
        try:
            identifier = cls.encode_gadget_identifier(gadget)
        except IdentifierEncodeError as err:
            self._logger.error(err.args[0])
            raise GadgetEncodeError(gadget.__class__.__name__, gadget.get_name(), f"Identifier is unknown")

        characteristics_json = [cls.encode_characteristic(x) for x in gadget.get_characteristics()]

        mapping_json = {}
        for mapping in gadget.get_event_mapping():
            if mapping.get_id() in mapping_json:
                cls._get_logger().error(f"found double mapping for {mapping.get_id()}")
                continue
            mapping_json[mapping.get_id()] = mapping.get_list()

        gadget_json = {"type": int(identifier),
                       "id": gadget.get_name(),
                       "characteristics": characteristics_json,
                       "event_map": mapping_json}

        return gadget_json

    @classmethod
    def encode_gadget_update(cls, gadget: Gadget) -> dict:
        """
        Serializes gadget update information according to api specification

        :param gadget: The gadget to serialize
        :return: The serialized version of the changeable gadget information as dict
        :raises GadgetEncodeError: If anything goes wrong during the serialization process
        """
        characteristics_json = [cls.encode_characteristic_update(x) for x in gadget.get_characteristics()]

        gadget_json = {"id": gadget.get_name(),
                       "characteristics": characteristics_json}

        return gadget_json

    @staticmethod
    def encode_gadget_identifier(gadget: RemoteGadget) -> GadgetIdentifier:
        """
        Gets a gadget identifier for the class of the passed gadget

        :param gadget: The gadget to get the identifier for
        :return: The gadget identifier
        :raises IdentifierEncodeError: If no Identifier for the gadget can be found
        """
        switcher = {
            "AnyGadget": GadgetIdentifier.any_gadget,
            "FanWestinghouseIR": GadgetIdentifier.fan_westinghouse_ir,
            "LampNeopixelBasic": GadgetIdentifier.lamp_neopixel_rgb_basic
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
                "step_value": characteristic.get_step_value()}

    @staticmethod
    def encode_characteristic_update(characteristic: Characteristic) -> dict:
        """
        Serializes a characteristic update information according to api specification

        :param characteristic: The characteristic to serialize
        :return: The serialized version of the the changeable characteristic information as dict
        """
        return {"type": int(characteristic.get_type()),
                "step_value": characteristic.get_step_value()}

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
                "platformio_version": bridge_info.pio_version,
                "git_version": bridge_info.git_version,
                "python_version": bridge_info.python_version,
                "pipenv_version": bridge_info.pipenv_version}

    @staticmethod
    def encode_bridge_update_info(update_info: Tuple[str, str, str, str, str, int]) -> dict:
        """
        Serializes bridge information according to api specification

        :param update_info: bridge update information
        :return:
        """
        curr_hash, new_hash, branch_name, curr_date, new_date, num_commits = update_info
        return {"current_commit_hash": curr_hash,
                "new_commit_hash": new_hash,
                "current_branch_name": branch_name,
                "current_branch_release_date": curr_date,
                "new_branch_release_date": new_date,
                "num_commits_between_branches": num_commits}

    def encode_all_gadgets_info(self, remote_gadgets: list[RemoteGadget], local_gadgets: list[LocalGadget]) -> dict:
        remote_gadget_data = []
        for gadget in remote_gadgets:
            try:
                remote_gadget_data.append(self.encode_gadget(gadget))
            except GadgetEncodeError as err:
                self._logger.error(err.args[0])

        local_gadget_data = []
        for gadget in local_gadgets:
            try:
                local_gadget_data.append(self.encode_gadget(gadget))
            except GadgetEncodeError as err:
                self._logger.error(err.args[0])

        return {"remote": remote_gadget_data,
                "local": local_gadget_data}

    @classmethod
    def encode_all_clients_info(cls, client_info: list[Client]) -> dict:
        client_data = []
        for client in client_info:
            try:
                client_data.append(cls.encode_client(client))
            except GadgetEncodeError:
                cls._get_logger().error(f"Failed to encode client '{client.get_name()}'")
        return {"clients": client_data}

    @staticmethod
    def encode_gadget_publisher(publisher: GadgetPublisher) -> dict:
        try:
            out_data = {
                "type": _gadget_publisher_name_mapping[publisher.__class__]
            }
        except KeyError:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)

        if isinstance(publisher, GadgetPublisherHomekit):
            config_data = publisher.config.data
            if config_data is not None:
                out_data["pairing_pin"] = config_data["accessory_pin"]
                out_data["port"] = config_data["host_port"]
                out_data["name"] = config_data["name"]
        else:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)
        return out_data

    @classmethod
    def encode_gadget_publisher_list(cls, publishers: list[GadgetPublisher]):
        buf_list = []
        for publisher in publishers:
            try:
                buf_list.append(cls.encode_gadget_publisher(publisher))
            except GadgetPublisherEncodeError as err:
                cls._get_logger().error(err.args[0])
        return {
            "gadget_publishers": buf_list
        }
