from datetime import datetime

from gadgets.remote.lamp_rgb import LampRGB
from lib.logging_interface import ILogging
from gadgets.remote.remote_gadget import RemoteGadget
from system.gadget_definitions import GadgetIdentifier, GadgetClass, GadgetClassMapping
from smarthome_bridge.client import Client
from system.utils.software_version import SoftwareVersion

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class GadgetDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding gadget")


class CharacteristicDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding characteristic")


class ClientDecodeError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Error decoding client: {message}")


class ApiDecoder(ILogging):
    def __init__(self):
        super().__init__()

    def decode_remote_gadget(self, gadget_data: dict, host: str) -> RemoteGadget:
        """
        Decodes a gadget out of the data given

        :param gadget_data: The json data to parse the gadget from
        :param host: Host-Client of the gadget
        :return: The parsed gadget
        :raises GadgetDecodeError: If anything goes wrong decoding the gadget
        """
        try:
            identifier = GadgetIdentifier(gadget_data["type"])
            gadget_class = None
            for g_class, types in GadgetClassMapping:
                if identifier in types:
                    gadget_class = g_class

            if gadget_class is None:
                raise GadgetDecodeError()

            if gadget_class == GadgetClass.lamp_rgb:
                return LampRGB(gadget_data["id"],
                               host)
            else:
                raise GadgetDecodeError()

        except (KeyError, ValueError) as err:
            self._logger.error(err.args[0])
            raise GadgetDecodeError()

    def decode_client(self, client_data: dict, client_name: str) -> Client:
        """
        Parses a smarthome-client from the given data

        :param client_data: Data to parse the client from
        :param client_name: Name of the client
        :return: The parsed client
        :raises ClientDecodeError: If anything goes wrong parsing the client
        """
        try:
            runtime_id = client_data["runtime_id"]
            flash_date = None
            if client_data["sw_uploaded"] is not None:
                date_str = client_data["sw_uploaded"]
                try:
                    flash_date = datetime.strptime(client_data["sw_uploaded"], DATETIME_FORMAT)
                except ValueError:
                    self._logger.error(f"Cannot decode datetime string '{date_str}' using '{DATETIME_FORMAT}'")
            software_commit = client_data["sw_commit"]
            software_branch = client_data["sw_branch"]
            port_mapping = client_data["port_mapping"]
            boot_mode = client_data["boot_mode"]
            api_version = SoftwareVersion.from_string(client_data["api_version"])

            out_client = Client(client_name,
                                runtime_id,
                                flash_date,
                                software_commit,
                                software_branch,
                                port_mapping,
                                boot_mode,
                                api_version)
            return out_client
        except KeyError as err:
            raise ClientDecodeError(f"Key Error at '{err.args[0]}'")
