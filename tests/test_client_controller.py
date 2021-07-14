import pytest

from client_controller import ClientController, NoClientResponseException
from test_helpers.mock_network_connector import MockNetworkConnector
from client_config_manager import ClientConfigManager
from json_validator import ValidationError

TEST_SENDER_NAME = "pytest_sender"
TEST_CLIENT_NAME = "pytest_client"
BROKEN_CONFIG = {"status": "broken af"}
WORKING_CONFIG_NAME = "Example"


@pytest.fixture
def connector():
    connector = MockNetworkConnector(TEST_SENDER_NAME)
    yield connector
    connector.__del__()


@pytest.fixture
def manager():
    manager = ClientConfigManager()
    yield manager


def test_client_controller_reboot(connector: MockNetworkConnector, manager: ClientConfigManager):
    controller = ClientController(TEST_CLIENT_NAME, connector)
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


def test_client_controller_reset_config(connector: MockNetworkConnector, manager: ClientConfigManager):
    controller = ClientController(TEST_CLIENT_NAME, connector)
    try:
        controller.reset_config()
    except NoClientResponseException:
        pass
    else:
        assert False

    connector.reset()

    try:
        connector.mock_ack(True)
        result = controller.reset_config()
    except NoClientResponseException:
        assert False
    else:
        assert result is True


def test_client_controller_write_config(connector: MockNetworkConnector, manager: ClientConfigManager):
    controller = ClientController(TEST_CLIENT_NAME, connector)
    working_config = manager.get_config(WORKING_CONFIG_NAME)
    assert working_config is not None

    try:
        controller.write_config(BROKEN_CONFIG)
    except ValidationError:
        pass
    else:
        assert False

    connector.reset()

    try:
        controller.write_config(working_config)
    except NoClientResponseException:
        pass
    else:
        assert False

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
