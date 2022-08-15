import datetime
from typing import Optional

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.client import Client
from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from smarthome_bridge.status_supplier_interfaces.client_status_supplier import ClientStatusSupplier, \
    ClientDoesntExistsError
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier


class DummyGadgetStatusSupplier(GadgetStatusSupplier):
    mock_gadgets: list[Gadget]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_gadgets = []

    def get_gadget(self, gadget_id: str) -> Optional[Gadget]:
        for gadget in self.mock_gadgets:
            if gadget.id == gadget_id:
                return gadget
        return None

    def add_gadget(self, gadget: Gadget):
        self.mock_gadgets.append(gadget)

    def _get_gadgets(self) -> list[Gadget]:
        return self.mock_gadgets


class DummyClientStatusSupplier(ClientStatusSupplier):
    mock_clients: list[Client]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_clients = []

    def _get_clients(self) -> list[Client]:
        return self.mock_clients

    def add_client(self, client: Client) -> None:
        self.mock_clients.append(client)

    def remove_client(self, client_id: str) -> None:
        for client in self.mock_clients:
            if client.id == client_id:
                self.mock_clients.remove(client)
                return
        raise ClientDoesntExistsError(client_id)

    def get_client(self, client_id: str) -> Client:
        for client in self.mock_clients:
            if client.id == client_id:
                return client
        raise ClientDoesntExistsError(client_id)


class DummyBridgeStatusSupplier(BridgeStatusSupplier):

    def __init__(self, info: BridgeInformationContainer):
        super().__init__()
        self.mock_info = info

    def _get_info(self) -> BridgeInformationContainer:
        return self.mock_info


class DummyGadgetPublisher(GadgetPublisher):
    mock_last_update: Optional[GadgetUpdateContainer]
    mock_add_gadget: Optional[str]
    mock_remove_gadget: Optional[str]

    def __init__(self):
        super().__init__()
        self.reset()

    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        self.mock_last_update = update_container

    def add_gadget(self, gadget_id: str):
        self.mock_add_gadget = gadget_id

    def remove_gadget(self, gadget_id: str):
        self.mock_remove_gadget = gadget_id

    def reset(self):
        self.mock_last_update = None
        self.mock_add_gadget = None
        self.mock_remove_gadget = None


class DummyGadgetPublisherStatusSupplier(GadgetPublisherStatusSupplier):
    mock_publishers: list[GadgetPublisher]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_publishers = []

    def _get_publishers(self) -> list[GadgetPublisher]:
        return self.mock_publishers
