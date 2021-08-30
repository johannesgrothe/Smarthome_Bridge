from datetime import datetime
from logging_interface import LoggingInterface
from gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from gadgets.gadget_factory import GadgetFactory
from smarthome_bridge.smarthomeclient import SmarthomeClient


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class GadgetDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding gadget")


class CharacteristicDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding characteristic")


class ClientDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding client")


class ApiDecoder(LoggingInterface):
    def __init__(self):
        super().__init__()

    def decode_gadget(self, gadget_data: dict, host: str) -> Gadget:
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

            name = gadget_data["name"]
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
            value = characteristic_data["val"]
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

    def decode_client(self, client_data: dict, client_name: str) -> SmarthomeClient:
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

            out_client = SmarthomeClient(client_name,
                                         runtime_id,
                                         flash_date,
                                         software_commit,
                                         software_branch,
                                         port_mapping,
                                         boot_mode)
            return out_client
        except KeyError as err:
            self._logger.error(err.args[0])
            raise ClientDecodeError
