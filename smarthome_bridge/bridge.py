import logging
import os
import threading
from datetime import datetime

from smarthome_bridge.local_gadget_manager import LocalGadgetManager
from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from utils.auth_manager import AuthManager
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.client_manager import ClientManager
from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.gadget_manager import GadgetManager
from utils.repository_manager import RepositoryManager, RepositoryStatusException
from utils.system_info_tools import SystemInfoTools
from utils.user_manager import UserManager


class Bridge(BridgeStatusSupplier):

    _logger: logging.Logger

    _network_manager: NetworkManager
    _client_manager: ClientManager
    _gadget_manager: GadgetManager
    _local_gadgets: LocalGadgetManager
    api: ApiManager

    _gadget_sync_lock: threading.Lock
    _bridge_info: BridgeInformationContainer

    def __init__(self, name: str, data_directory: str):
        super().__init__()
        self._logger = logging.getLogger(f"{self.__class__.__name__}[{name}]")
        self._logger.info("Starting bridge")
        self._network_manager = NetworkManager()
        self._client_manager = ClientManager()
        self._gadget_manager = GadgetManager()
        self._local_gadgets = LocalGadgetManager()
        self._gadget_sync_lock = threading.Lock()
        self.api = ApiManager(self, self._network_manager)
        auth_manager = AuthManager(UserManager(data_directory))
        self.api.auth_manager = auth_manager

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
        self.api.__del__()
        self._network_manager.__del__()
        self._client_manager.__del__()
        self._gadget_manager.__del__()

    @property
    def info(self) -> BridgeInformationContainer:
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
