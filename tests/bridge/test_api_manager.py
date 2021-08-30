import pytest

from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.client_manager import ClientManager
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.gadget_manager import GadgetManager


@pytest.fixture()
def clients():
    clients = ClientManager()
    yield clients
    clients.__del__()


@pytest.fixture()
def network_manager():
    manager = NetworkManager()
    yield manager
    manager.__del__()


@pytest.fixture()
def gadget_manager():
    manager = GadgetManager()
    yield manager
    manager.__del__()


@pytest.fixture()
def api(clients: ClientManager, network_manager):
    api = ApiManager(clients, network_manager)
    yield api
    api.__del__()


@pytest.mark.bridge
def test_api(api: ApiManager):
    assert api._clients.get_client_count() == 0
