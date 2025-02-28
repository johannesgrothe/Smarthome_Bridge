"""Module to contain the ClientController and its exceptions"""
from lib.logging_interface import ILogging
from network.request import NoClientResponseException

from system.api_definitions import ApiURIs
from smarthome_bridge.network_manager import NetworkManager

from toolkit.client_eol_config import ClientEolConfig
from toolkit.client_system_config import ClientSystemConfig


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


class ClientController(ILogging):
    """Class to control all means of a hardware client connected to the network"""

    _client_id: str
    _network: NetworkManager

    def __init__(self, client_id: str, network: NetworkManager):
        super().__init__()
        self._client_id = client_id
        self._network = network

    def reboot_client(self):
        """Reboots the client to make changes take effect.

        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ClientRebootError: If rebooting fails for any reason
        """

        payload = {"subject": "reboot"}

        res = self._network.send_request(ApiURIs.system_ctrl.uri, self._client_id, payload)
        if not res:
            raise NoClientResponseException()
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
            raise NoClientResponseException()
        if not res.get_ack():
            raise ConfigEraseError(self._client_id)

    def write_system_config(self, system_config: ClientSystemConfig):
        """
        Writes a system config to the client

        :param system_config: Config to write
        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigWriteError: If writing the config fails for any reason
        :raises ValidationError: If passed config was faulty
        """
        res = self._network.send_request(ApiURIs.client_system_config_write.uri,
                                         self._client_id,
                                         system_config.to_dict())
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigWriteError(self._client_id)

    def write_eol_config(self, system_config: ClientEolConfig):
        """
        Writes a system config to the client

        :param system_config: Config to write
        :return: None
        :raises NoClientResponseException: If client does not respond
        :raises ConfigWriteError: If writing the config fails for any reason
        :raises ValidationError: If passed config was faulty
        """
        res = self._network.send_request(ApiURIs.client_system_config_write.uri,
                                         self._client_id,
                                         system_config.to_dict())
        if not res:
            raise NoClientResponseException
        if not res.get_ack():
            raise ConfigWriteError(self._client_id)
