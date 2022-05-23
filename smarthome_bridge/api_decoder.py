from datetime import datetime
from lib.logging_interface import LoggingInterface
from gadgets.remote_gadget import RemoteGadget
from system.gadget_definitions import GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from gadgets.gadget_factory import GadgetFactory
from smarthome_bridge.client import Client
from smarthome_bridge.gadget_update_information import GadgetUpdateInformation, CharacteristicUpdateInformation
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


class ApiDecoder(LoggingInterface):
    def __init__(self):
        super().__init__()

    def decode_gadget(self, gadget_data: dict, host: str) -> RemoteGadget:
        """
        Decodes a gadget out of the data given

        :param gadget_data: The json data to parse the gadget from
        :param host: Host-Client of the gadget
        :return: The parsed gadget
        :raises GadgetDecodeError: If anything goes wrong decoding the gadget
        """
        try:
            identifier = GadgetIdentifier(gadget_data["type"])

            self._logger.info(f"Decoding gadget of type '{identifier}'")

            name = gadget_data["id"]
            characteristics = [self.decode_characteristic(data) for data in gadget_data["characteristics"]]
            factory = GadgetFactory()
            out_gadget = factory.create_gadget(identifier,
                                               name,
                                               host,
                                               characteristics)
            return out_gadget
        except (KeyError, ValueError, CharacteristicDecodeError) as err:
            self._logger.error(err.args[0])
            raise GadgetDecodeError()

    def decode_characteristic(self, characteristic_data: dict) -> Characteristic:
        """
        Parses a characteristic from the given data

        :param characteristic_data: Data to parse the characteristic from
        :return: The parsed Characteristic
        :raises CharacteristicDecodeError: If anything goes wrong parsing the characteristic
        """
        try:
            identifier = CharacteristicIdentifier(characteristic_data["type"])
            min_val = characteristic_data["min"]
            max_val = characteristic_data["max"]
            steps = characteristic_data["steps"]
            value = characteristic_data["step_value"]
            return Characteristic(identifier,
                                  min_val,
                                  max_val,
                                  steps,
                                  value)
        except KeyError:
            self._logger.error("Missing key in data for characteristic")
        except ValueError:
            self._logger.error(f"Cannot create CharacteristicIdentifier out of '{characteristic_data['type']}'")
        raise CharacteristicDecodeError

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

    def decode_characteristic_update(self, characteristic_data: dict) -> CharacteristicUpdateInformation:
        """
        Decodes characteristic update information into an object representing the same data

        :param characteristic_data: Data about the characteristic to update
        :return: A characteristic update container
        :raises CharacteristicDecodeError: If anything goes wrong during decoding
        """

        try:
            identifier = CharacteristicIdentifier(characteristic_data["type"])
            value = characteristic_data["step_value"]
            return CharacteristicUpdateInformation(identifier,
                                                   value)
        except KeyError:
            self._logger.error("Missing key in data for characteristic")
        except ValueError:
            self._logger.error(f"Cannot create CharacteristicIdentifier out of '{characteristic_data['type']}'")
        raise CharacteristicDecodeError

    def decode_gadget_update(self, gadget_data: dict) -> GadgetUpdateInformation:
        """
        Decodes a gadget update information container from a json

        :param gadget_data: The json data to parse the gadget update info from
        :return: The parsed gadget update information container
        :raises GadgetDecodeError: If anything goes wrong decoding
        """
        try:
            name = gadget_data["id"]

            characteristics = [self.decode_characteristic_update(data) for data in gadget_data["characteristics"]]
            return GadgetUpdateInformation(name,
                                           characteristics)
        except (KeyError, CharacteristicDecodeError) as err:
            self._logger.error(err.args[0])
            raise GadgetDecodeError

