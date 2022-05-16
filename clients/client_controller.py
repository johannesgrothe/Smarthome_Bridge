"""Module to contain the ClientController and its exceptions"""
from lib.logging_interface import LoggingInterface
from network.request import NoClientResponseException

from system.api_definitions import ApiURIs
from smarthome_bridge.network_manager import NetworkManager
from utils.json_validator import Validator


class ClientRebootError(Exception):
    """Error to be thrown if rebooting the client fails for any reason"""

    def __init__(self, client_id: str):
        super().__init__(f"Error rebooting {client_id}")


class ConfigEraseError(Exception):
    """Error to be thrown if erasing configs fails for any reason"""

    def __init__(self, client_id: str):
        super().__init__(f"Error erasing configs on {client_id}")


class ConfigWriteError(Exception):
    """Error to be thrown if writing any config fails for any reason"""

    def __init__(self, client_id: str):
        super().__init__(f"Error writing config on {client_id}")


class ClientController(LoggingInterface):
    """Class to control all means of a hardware client connected to the network"""

    _client_id: str
    _network: NetworkManager
    _validator: Validator

    def __init__(self, client_id: str, network: NetworkManager):
        super().__init__()
        self._client_id = client_id
        self._network = network
        self._validator = Validator()

    def reboot_client(self):
        """Reboots the client to make changes take effect.

        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ClientRebootError: If rebooting fails for any reason
        """

        payload = {"subject": "reboot"}

        res = self._network.send_request(ApiURIs.client_reboot.uri, self._client_id, payload)
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ClientRebootError(self._client_id)

    def erase_config(self):
        """
        Erases all configs from the client

        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigEraseError: If erasing fails for any reason
        """
        res = self._network.send_request(ApiURIs.client_config_delete.uri, self._client_id, {})
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigEraseError(self._client_id)

    def write_system_config(self, system_config: dict):
        """
        Writes a system config to the client

        :param system_config: Config to write
        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigWriteError: If writing the config fails for any reason
        :raises ValidationError: If passed config was faulty
        """
        self._validator.validate(system_config, "client_system_config")
        res = self._network.send_request(ApiURIs.client_system_config_write.uri,
                                         self._client_id,
                                         system_config)
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigWriteError(self._client_id)

    def write_event_config(self, event_config: dict):
        """
        Writes a system config to the client

        :param event_config: Config to write
        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigWriteError: If writing the config fails for any reason
        :raises ValidationError: If passed config was faulty
        """
        self._validator.validate(event_config, "client_event_config")
        res = self._network.send_request(ApiURIs.client_event_config_write.uri,
                                         self._client_id,
                                         event_config)
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigWriteError(self._client_id)

    def write_gadget_config(self, gadget_config: dict):
        """
        Writes a system config to the client

        :param gadget_config: Config to write
        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigWriteError: If writing the config fails for any reason
        :raises ValidationError: If passed config was faulty
        """
        self._validator.validate(gadget_config, "client_gadget_config")
        res = self._network.send_request(ApiURIs.client_gadget_config_write.uri,
                                         self._client_id,
                                         gadget_config)
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigWriteError(self._client_id)
