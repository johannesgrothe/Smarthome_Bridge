from typing import Callable

import pytest
from jsonschema import ValidationError

from clients.client_controller import ClientController, NoClientResponseException, ClientRebootError, \
    ConfigEraseError, ConfigWriteError
from test_helpers.dummy_network_connector import DummyNetworkConnector
from utils.client_config_manager import ClientConfigManager
from smarthome_bridge.network_manager import NetworkManager

TEST_SENDER_NAME = "pytest_sender"
TEST_CLIENT_NAME = "pytest_client"
BROKEN_CONFIG = {"status": "broken af"}
WORKING_CONFIG_NAME = "Example"


def config_write_test_helper(write_method: Callable[[dict], None], config: dict, connector: DummyNetworkConnector):
    assert config is not None

    with pytest.raises(ValidationError):
        write_method(BROKEN_CONFIG)

    connector.reset()

    with pytest.raises(NoClientResponseException):
        write_method(config)

    connector.reset()

    connector.mock_ack(False)
    with pytest.raises(ConfigWriteError):
        write_method(config)

    connector.reset()

    connector.mock_ack(True)
    write_method(config)


@pytest.fixture()
def connector():
    connector = DummyNetworkConnector(TEST_SENDER_NAME)
    yield connector
    connector.__del__()


@pytest.fixture
def network(connector):
    manager = NetworkManager()
    manager.add_connector(connector)
    manager.set_default_timeout(2)
    yield manager
    manager.__del__()


@pytest.fixture
def manager():
    manager = ClientConfigManager()
    yield manager


@pytest.fixture
def controller(network):
    controller = ClientController(TEST_CLIENT_NAME, network)
    yield controller


def test_client_controller_reboot(controller: ClientController, manager: ClientConfigManager,
                                  connector: DummyNetworkConnector):
    with pytest.raises(NoClientResponseException):
        controller.reboot_client()

    connector.reset()

    connector.mock_ack(False)
    with pytest.raises(ClientRebootError):
        controller.reboot_client()

    connector.reset()

    connector.mock_ack(True)
    controller.reboot_client()


def test_client_controller_reset_config(controller: ClientController, connector: DummyNetworkConnector,
                                        manager: ClientConfigManager):
    with pytest.raises(NoClientResponseException):
        controller.erase_config()

    connector.reset()

    connector.mock_ack(False)
    with pytest.raises(ConfigEraseError):
        controller.erase_config()

    connector.reset()

    connector.mock_ack(True)
    controller.erase_config()


def test_client_controller_write_system_config(controller: ClientController, connector: DummyNetworkConnector,
                                               manager: ClientConfigManager):
    working_config = manager.get_config(WORKING_CONFIG_NAME)["system"]
    config_write_test_helper(controller.write_system_config, working_config, connector)


def test_client_controller_write_gadget_config(controller: ClientController, connector: DummyNetworkConnector,
                                               manager: ClientConfigManager):
    working_config = manager.get_config(WORKING_CONFIG_NAME)["gadgets"]
    config_write_test_helper(controller.write_gadget_config, working_config, connector)


def test_client_controller_write_event_config(controller: ClientController, connector: DummyNetworkConnector,
                                              manager: ClientConfigManager):
    working_config = manager.get_config(WORKING_CONFIG_NAME)["events"]
    config_write_test_helper(controller.write_event_config, working_config, connector)
