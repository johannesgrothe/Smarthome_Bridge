import pytest

from smarthome_bridge.client_manager import ClientManager


@pytest.fixture()
def manager():
    manager = ClientManager()
    yield manager
    manager.__del__()


@pytest.mark.bridge
def test_client_manager(manager: ClientManager):
    assert manager.get_client_count() == 0
