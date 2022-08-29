import logging
import os
import threading
from datetime import datetime
from typing import Optional

from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from smarthome_bridge.update.bridge_update_manager import BridgeUpdateManager
from utils.auth_manager import AuthManager
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.client_manager import ClientManager
from smarthome_bridge.api.api_manager import ApiManager, ApiManagerSetupContainer
from smarthome_bridge.gadget_manager import GadgetManager
from utils.client_config_manager import ClientConfigManager
from utils.repository_manager import RepositoryManager, RepositoryStatusException
from utils.system_info_tools import SystemInfoTools
from utils.user_manager import UserManager


class Bridge(BridgeStatusSupplier):
    _logger: logging.Logger

    _network_manager: NetworkManager
    _client_manager: ClientManager
    _gadget_manager: GadgetManager
    _api: ApiManager
    _bridge_info: BridgeInformationContainer

    def __init__(self, name: str, data_directory: str, update_manager: Optional[BridgeUpdateManager] = None):
        super().__init__()
        self._logger = logging.getLogger(f"{self.__class__.__name__}[{name}]")
        self._logger.info("Starting bridge")
        self._network_manager = NetworkManager()
        self._client_manager = ClientManager()
        self._gadget_manager = GadgetManager()

        self._api = ApiManager(ApiManagerSetupContainer(
            self._network_manager,
            self._gadget_manager,
            self._client_manager,
            self._gadget_manager,
            self,
            AuthManager(UserManager(data_directory)),
            update_manager,
            ClientConfigManager(os.path.join(data_directory, "configs"))
        ))

        self._gadget_manager.add_gadget_publisher(self._api.request_handler_gadget)

        try:
            repo_manager = RepositoryManager(os.getcwd(), None)
            g_branch = repo_manager.get_branch()
            g_hash = repo_manager.get_commit_hash()
        except RepositoryStatusException:
            # When deployed via docker, no repository information is copied since the bridge is a submodule
            g_branch = None
            g_hash = None
        self._bridge_info = BridgeInformationContainer(name,
                                                       g_branch,
                                                       g_hash,
                                                       datetime.now(),
                                                       SystemInfoTools.read_pio_version(),
                                                       SystemInfoTools.read_pipenv_version(),
                                                       SystemInfoTools.read_git_version(),
                                                       SystemInfoTools.read_python_version())

    def __del__(self):
        self._logger.info("Shutting down bridge")
        self._api.__del__()
        self._network_manager.__del__()
        self._client_manager.__del__()
        self._gadget_manager.__del__()

    def _get_info(self) -> BridgeInformationContainer:
        return self._bridge_info

    @property
    def network(self) -> NetworkManager:
        return self._network_manager

    @property
    def clients(self) -> ClientManager:
        return self._client_manager

    @property
    def gadgets(self) -> GadgetManager:
        return self._gadget_manager

    @property
    def api(self) -> ApiManager:
        return self._api
