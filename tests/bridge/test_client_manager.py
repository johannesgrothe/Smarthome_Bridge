import pytest

from smarthome_bridge.client_manager import *
from smarthome_bridge.client import Client

WRONG_CLIENT_NAME = "wrong_client"


@pytest.fixture()
def manager():
    manager = ClientManager()
    yield manager
    manager.__del__()


@pytest.mark.bridge
def test_client_manager(manager: ClientManager, f_client: Client):
    assert manager.get_client_count() == 0
    with pytest.raises(ClientDoesntExistsError):
        manager.get_client(f_client.id)

    manager.add_client(f_client)

    with pytest.raises(ClientDoesntExistsError):
        manager.get_client(WRONG_CLIENT_NAME)
    assert manager.get_client_count() == 1

    with pytest.raises(ClientAlreadyExistsError):
        manager.add_client(f_client)
    assert manager.get_client_count() == 1

    buf_client = manager.get_client(f_client.id)

    assert buf_client == f_client

    with pytest.raises(ClientDoesntExistsError):
        manager.remove_client(WRONG_CLIENT_NAME)

    manager.remove_client(f_client.id)

    assert manager.get_client_count() == 0

    manager.__del__()
