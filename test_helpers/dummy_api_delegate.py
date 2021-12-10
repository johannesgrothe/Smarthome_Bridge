from typing import Optional
from datetime import datetime

from gadgets.gadget import Gadget
from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.client import Client


class DummyApiDelegate(ApiManagerDelegate):

    _last_heartbeat_name = Optional[str]
    _last_heartbeat_runtime = Optional[int]
    _last_gadget: Optional[Gadget]
    _last_gadget_update: Optional[Gadget]
    _last_client: Optional[Client]

    _gadgets: list[Gadget]
    _clients: list[Client]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self._last_heartbeat_name = None
        self._last_heartbeat_runtime = None
        self._last_gadget = None
        self._last_gadget_update = None
        self._last_client = None
        self._clients = []
        self._gadgets = []

    def handle_heartbeat(self, client_name: str, runtime_id: int):
        self._last_heartbeat_name = client_name
        self._last_heartbeat_runtime = runtime_id

    def handle_gadget_update(self, gadget: Gadget):
        self._last_gadget_update = gadget

    def handle_gadget_sync(self, gadget: Gadget):
        self._last_gadget = gadget

    def handle_client_sync(self, client: Client):
        self._last_client = client

    def get_last_heartbeat_name(self) -> Optional[str]:
        return self._last_heartbeat_name

    def get_last_heartbeat_runtime(self) -> Optional[int]:
        return self._last_heartbeat_runtime

    def get_last_client(self) -> Optional[Client]:
        return self._last_client

    def get_last_gadget_update(self) -> Optional[Gadget]:
        return self._last_gadget_update

    def get_last_gadget(self) -> Optional[Gadget]:
        return self._last_gadget

    def add_gadget(self, gadget: Gadget):
        self._gadgets.append(gadget)

    def add_client(self, client: Client):
        self._clients.append(client)

    def get_bridge_info(self) -> BridgeInformationContainer:
        return BridgeInformationContainer("test_data",
                                          "develop",
                                          "abc1776",
                                          datetime.now(),
                                          "1.0.0",
                                          "1.1.0",
                                          "1.2.0",
                                          "1.3.0")

    def get_client_info(self) -> list[Client]:
        return self._clients

    def get_gadget_info(self) -> list[Gadget]:
        return self._gadgets
