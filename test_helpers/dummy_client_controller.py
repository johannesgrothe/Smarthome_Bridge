from clients.client_controller import ClientController
from smarthome_bridge.network_manager import NetworkManager


class DummyClientController(ClientController):
    def __init__(self, client_id: str, network: NetworkManager):
        super().__init__(client_id, network)

    def reboot_client(self):
        pass

    def erase_config(self):
        pass

    def write_system_config(self, system_config: dict):
        pass

    def write_event_config(self, event_config: dict):
        pass

    def write_gadget_config(self, gadget_config: dict):
        pass
