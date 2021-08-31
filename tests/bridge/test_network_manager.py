import pytest

from smarthome_bridge.network_manager import NetworkManager
from test_helpers.dummy_network_connector import DummyNetworkConnector

HOST_NAME = "test_connector"


@pytest.fixture()
def manager():
    manager = NetworkManager()
    yield manager
    manager.__del__()


@pytest.fixture()
def connector():
    connector = DummyNetworkConnector(HOST_NAME)
    yield connector
    connector.__del__()


@pytest.mark.bridge
def test_client_manager(manager: NetworkManager, connector: DummyNetworkConnector):
    assert manager.get_connector_count() == 0
    manager.add_connector(connector)
    assert manager.get_connector_count() == 1
    manager.add_connector(connector)
    assert manager.get_connector_count() == 1
    manager.remove_connector(connector)
    assert manager.get_connector_count() == 0
    manager.remove_connector(connector)
    assert manager.get_connector_count() == 0
