import logging
import os
import threading
from datetime import datetime

from gadget_publishers.gadget_publisher import GadgetPublisher
from utils.auth_manager import AuthManager
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.gadget_pubsub import GadgetUpdateSubscriber, GadgetUpdatePublisher
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.client_manager import ClientManager, ClientDoesntExistsError
from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.gadget_manager import GadgetManager

from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from gadgets.remote_gadget import RemoteGadget
from smarthome_bridge.client import Client
from utils.repository_manager import RepositoryManager, RepositoryStatusException
from utils.system_info_tools import SystemInfoTools
from utils.user_manager import UserManager


class Bridge(ApiManagerDelegate, GadgetUpdateSubscriber, GadgetUpdatePublisher):
    _logger: logging.Logger

    _network_manager: NetworkManager
    _client_manager: ClientManager
    _gadget_manager: GadgetManager
    _gadget_publishers: list[GadgetPublisher]
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
        self._gadget_publishers = []
        self._local_gadgets = LocalGadgetManager()
        self._gadget_sync_lock = threading.Lock()
        self.api = ApiManager(self, self._network_manager)
        auth_manager = AuthManager(UserManager(data_directory))
        self.api.set_auth_manager(auth_manager)
        self._gadget_manager.subscribe(self)

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
        for publisher in self._gadget_publishers:
            publisher.__del__()

    def get_network_manager(self):
        return self._network_manager

    def get_client_manager(self):
        return self._client_manager

    def get_gadget_manager(self):
        return self._gadget_manager

    def receive_gadget_update(self, gadget: RemoteGadget):
        self._logger.info(f"Forwarding update for {gadget.get_name()}")
        self.api.send_gadget_update(gadget)

    def receive_gadget(self, gadget: RemoteGadget):
        pass

    def add_gadget_publisher(self, publisher: GadgetPublisher):
        publisher_classes = [x.__class__ for x in self._gadget_publishers]
        if publisher.__class__ in publisher_classes:
            self._logger.error(f"{publisher.__class__.__name__} already present in publishers")
            return
        if publisher not in self._gadget_publishers:
            self._gadget_publishers.append(publisher)
            self._gadget_manager.add_gadget_publisher(publisher)

    # API delegation

    def handle_heartbeat(self, client_name: str, runtime_id: int):
        client = self._client_manager.get_client(client_name)
        if client:
            if client.get_runtime_id() != runtime_id:
                self.api.request_sync(client_name)
            else:
                client.trigger_activity()
        else:
            self.api.request_sync(client_name)

    def handle_gadget_sync(self, gadget: RemoteGadget):
        with self._gadget_sync_lock:
            self._gadget_manager.receive_gadget(gadget)

    def handle_gadget_update(self, gadget: RemoteGadget):
        with self._gadget_sync_lock:
            self._gadget_manager.receive_gadget_update(gadget)

    def handle_client_sync(self, client: Client):
        try:
            self._client_manager.remove_client(client.get_name())
        except ClientDoesntExistsError:
            pass
        self._client_manager.add_client(client)

    def get_bridge_info(self) -> BridgeInformationContainer:
        return self._bridge_info

    def get_client_info(self) -> list[Client]:
        return [self._client_manager.get_client(x)
                for x
                in self._client_manager.get_client_ids()
                if self._client_manager.get_client(x) is not None]

    def get_gadget_info(self) -> list[RemoteGadget]:
        return [self._gadget_manager.get_gadget(x)
                for x
                in self._gadget_manager.get_gadget_ids()
                if self._gadget_manager.get_gadget(x) is not None]

    def get_gadget_publisher_info(self) -> list[GadgetPublisher]:
        return self._gadget_publishers

    def get_local_gadget_info(self) -> list[LocalGadget]:
        return self._local_gadgets.gadgets
