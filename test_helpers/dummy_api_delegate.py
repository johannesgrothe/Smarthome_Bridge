from typing import Optional

from gadgets.gadget import Gadget
from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from smarthome_bridge.smarthomeclient import SmarthomeClient


class DummyApiDelegate(ApiManagerDelegate):

    _last_heartbeat_name = Optional[str]
    _last_heartbeat_runtime = Optional[int]
    _last_gadget: Optional[Gadget]
    _last_client: Optional[SmarthomeClient]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self._last_heartbeat_name = None
        self._last_heartbeat_runtime = None
        self._last_gadget = None
        self._last_client = None

    def handle_heartbeat(self, client_name: str, runtime_id: int):
        self._last_heartbeat_name = client_name
        self._last_heartbeat_runtime = runtime_id

    def handle_gadget_update(self, gadget: Gadget):
        self._last_gadget = gadget

    def handle_client_update(self, client: SmarthomeClient):
        self._last_client = client

    def get_last_heartbeat_name(self) -> Optional[str]:
        return self._last_heartbeat_name

    def get_last_heartbeat_runtime(self) -> Optional[int]:
        return self._last_heartbeat_runtime

    def get_last_client(self) -> Optional[SmarthomeClient]:
        return self._last_client

    def get_last_gadget(self) -> Optional[Gadget]:
        return self._last_gadget
