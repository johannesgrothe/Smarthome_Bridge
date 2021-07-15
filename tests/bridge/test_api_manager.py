import pytest

from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.client_manager import ClientManager


@pytest.fixture()
def clients():
    clients = ClientManager()
    yield clients
    clients.__del__()


@pytest.fixture()
def api(clients: ClientManager):
    api = ApiManager(clients)
    yield api
    api.__del__()


@pytest.mark.bridge
def test_api(api: ApiManager):
    assert api._clients.get_client_count() == 0
