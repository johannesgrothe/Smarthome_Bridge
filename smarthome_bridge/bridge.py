import logging

from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.client_manager import ClientManager
from smarthome_bridge.api_manager import ApiManager


class Bridge:
    _logger: logging.Logger
    _name: str

    _network_manager: NetworkManager
    _client_manager: ClientManager
    _api: ApiManager

    def __init__(self, name: str):
        self._name = name
        self._logger = logging.getLogger(f"Bridge[{self._name}]")
        self._logger.info("Starting bridge")
        self._network_manager = NetworkManager()
        self._client_manager = ClientManager()
        self._api = ApiManager(self._client_manager, self._network_manager)

    def __del__(self):
        self._logger.info("Shutting down bridge")

    def get_name(self):
        return self._name

    def get_network_manager(self):
        return self._network_manager

    def get_client_manager(self):
        return self._client_manager
