from typing import Optional, Type

from clients.client_controller import ClientController
from smarthome_bridge.network_manager import NetworkManager

_mock_error: Optional[Exception] = None


class DummyClientController(ClientController):
    def __init__(self, client_id: str, network: NetworkManager):
        super().__init__(client_id, network)

    @staticmethod
    def set_error(err: Optional[Exception]):
        global _mock_error
        _mock_error = err

    def reboot_client(self):
        global _mock_error
        if _mock_error is not None:
            raise _mock_error

    def erase_config(self):
        global _mock_error
        if _mock_error is not None:
            raise _mock_error

    def write_system_config(self, system_config: dict):
        global _mock_error
        if _mock_error is not None:
            raise _mock_error

    def write_event_config(self, event_config: dict):
        global _mock_error
        if _mock_error is not None:
            raise _mock_error

    def write_gadget_config(self, gadget_config: dict):
        global _mock_error
        if _mock_error is not None:
            raise _mock_error
