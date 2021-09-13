import pytest
import random

from smarthome_bridge.client_manager import *
from smarthome_bridge.smarthomeclient import SmarthomeClient


TEST_CLIENT_NAME = "test_client"
WRONG_CLIENT_NAME = "wrong_client"


@pytest.fixture()
def manager():
    manager = ClientManager()
    yield manager
    manager.__del__()


@pytest.fixture()
def test_client():
    client = SmarthomeClient(TEST_CLIENT_NAME,
                             random.randint(0, 10000),
                             None,
                             None,
                             None,
                             {},
                             1)
    yield client
    # client.__del__()


@pytest.mark.bridge
def test_client_manager(manager: ClientManager, test_client: SmarthomeClient):
    assert manager.get_client_count() == 0
    assert manager.get_client(TEST_CLIENT_NAME) is None

    manager.add_client(test_client)

    assert manager.get_client(WRONG_CLIENT_NAME) is None
    assert manager.get_client_count() == 1

    with pytest.raises(ClientAlreadyExistsError):
        manager.add_client(test_client)
    assert manager.get_client_count() == 1

    buf_client = manager.get_client(TEST_CLIENT_NAME)

    assert buf_client.get_name() == TEST_CLIENT_NAME

    with pytest.raises(ClientDoesntExistsError):
        manager.remove_client(WRONG_CLIENT_NAME)

    manager.remove_client(test_client.get_name())

    assert manager.get_client_count() == 0

    manager.add_client(test_client)

    manager.__del__()
