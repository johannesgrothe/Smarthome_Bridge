import logging
import os
import threading
from datetime import datetime

from auth_manager import AuthManager
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.gadget_pubsub import GadgetUpdateSubscriber, GadgetUpdatePublisher
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.client_manager import ClientManager, ClientDoesntExistsError
from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.gadget_manager import GadgetManager

from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from gadgets.gadget import Gadget
from smarthome_bridge.client import Client
from repository_manager import RepositoryManager
from system_info_tools import SystemInfoTools
from user_manager import UserManager


class Bridge(ApiManagerDelegate, GadgetUpdateSubscriber, GadgetUpdatePublisher):

    _logger: logging.Logger
    _name: str
    _running_since: datetime

    _network_manager: NetworkManager
    _client_manager: ClientManager
    _gadget_manager: GadgetManager
    _api: ApiManager

    _gadget_sync_lock: threading.Lock

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._running_since = datetime.now()
        self._logger = logging.getLogger(f"Bridge[{self._name}]")
        self._logger.info("Starting bridge")
        self._network_manager = NetworkManager()
        self._client_manager = ClientManager()
        self._gadget_manager = GadgetManager()
        self._gadget_sync_lock = threading.Lock()
        self._api = ApiManager(self, self._network_manager)
        auth_manager = AuthManager(UserManager())
        self._api.set_auth_manager(auth_manager)
        self._gadget_manager.subscribe(self)

    def __del__(self):
        self._logger.info("Shutting down bridge")

    def get_name(self):
        return self._name

    def get_network_manager(self):
        return self._network_manager

    def get_client_manager(self):
        return self._client_manager

    def get_gadget_manager(self):
        return self._gadget_manager

    def receive_gadget_update(self, gadget: Gadget):
        self._logger.info(f"Forwarding update for {gadget.get_name()}")
        self._api.send_gadget_update(gadget)

    def receive_gadget(self, gadget: Gadget):
        pass

    # API delegation

    def handle_heartbeat(self, client_name: str, runtime_id: int):
        client = self._client_manager.get_client(client_name)
        if client:
            if client.get_runtime_id() != runtime_id:
                self._api.request_sync(client_name)
            else:
                client.trigger_activity()
        else:
            self._api.request_sync(client_name)

    def handle_gadget_sync(self, gadget: Gadget):
        with self._gadget_sync_lock:
            self._gadget_manager.receive_gadget(gadget)

    def handle_gadget_update(self, gadget: Gadget):
        with self._gadget_sync_lock:
            self._gadget_manager.receive_gadget_update(gadget)

    def handle_client_sync(self, client: Client):
        try:
            self._client_manager.remove_client(client.get_name())
        except ClientDoesntExistsError:
            pass
        self._client_manager.add_client(client)

    def get_bridge_info(self) -> BridgeInformationContainer:
        repo_manager = RepositoryManager(os.getcwd(), None)
        return BridgeInformationContainer(self._name,
                                          repo_manager.get_branch(),
                                          repo_manager.get_commit_hash(),
                                          self._running_since,
                                          SystemInfoTools.read_pio_version(),
                                          SystemInfoTools.read_pipenv_version(),
                                          SystemInfoTools.read_git_version(),
                                          SystemInfoTools.read_python_version())

    def get_client_info(self) -> list[Client]:
        return [self._client_manager.get_client(x)
                for x
                in self._client_manager.get_client_ids()
                if self._client_manager.get_client(x) is not None]

    def get_gadget_info(self) -> list[Gadget]:
        return [self._gadget_manager.get_gadget(x)
                for x
                in self._gadget_manager.get_gadget_ids()
                if self._gadget_manager.get_gadget(x) is not None]

