import pytest

from toolkit.client_controller import ClientController, NoClientResponseException
from test_helpers.dummy_network_connector import DummyNetworkConnector
from client_config_manager import ClientConfigManager
from json_validator import ValidationError
from smarthome_bridge.network_manager import NetworkManager

TEST_SENDER_NAME = "pytest_sender"
TEST_CLIENT_NAME = "pytest_client"
BROKEN_CONFIG = {"status": "broken af"}
WORKING_CONFIG_NAME = "Example"


@pytest.fixture()
def connector():
    connector = DummyNetworkConnector(TEST_SENDER_NAME)
    yield connector
    connector.__del__()


@pytest.fixture
def network(connector):
    manager = NetworkManager()
    manager.add_connector(connector)
    yield manager
    manager.__del__()


@pytest.fixture
def manager():
    manager = ClientConfigManager()
    yield manager


def test_client_controller_reboot(network: NetworkManager, manager: ClientConfigManager,
                                  connector: DummyNetworkConnector):
    controller = ClientController(TEST_CLIENT_NAME, network)
    try:
        controller.reboot_client()
    except NoClientResponseException:
        pass
    else:
        assert False

    connector.reset()

    try:
        connector.mock_ack(True)
        result = controller.reboot_client()
    except NoClientResponseException:
        assert False
    else:
        assert result is True


def test_client_controller_reset_config(network: NetworkManager, connector: DummyNetworkConnector, manager: ClientConfigManager):
    controller = ClientController(TEST_CLIENT_NAME, network)
    with pytest.raises(NoClientResponseException):
        controller.reset_config()

    connector.reset()

    try:
        connector.mock_ack(True)
        result = controller.reset_config()
    except NoClientResponseException:
        assert False
    else:
        assert result is True


def test_client_controller_write_config(network: NetworkManager, connector: DummyNetworkConnector, manager: ClientConfigManager):
    controller = ClientController(TEST_CLIENT_NAME, network)
    working_config = manager.get_config(WORKING_CONFIG_NAME)
    assert working_config is not None

    with pytest.raises(ValidationError):
        controller.write_config(BROKEN_CONFIG)

    connector.reset()

    with pytest.raises(NoClientResponseException):
        controller.write_config(working_config)

    connector.reset()

    try:
        connector.mock_ack(True)
        result = controller.write_config(working_config)
    except NoClientResponseException:
        assert False
    else:
        assert result is True

    connector.reset()

    try:
        connector.mock_ack(False)
        result = controller.write_config(working_config)
    except NoClientResponseException:
        assert False
    else:
        assert result is False
