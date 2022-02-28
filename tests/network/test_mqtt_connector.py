import pytest

from network.mqtt_connector import MQTTConnector
from test_helpers.echo_client import TestEchoClient
from tests.network.connector_tests import send_test, broadcast_test, broadcast_single_response_test
from smarthome_bridge.network_manager import NetworkManager

TEST_ECHO_CLIENT_NAME = "pytest_echo_client"
TEST_SENDER_NAME = "pytest_sender"

TEST_CHANNEL = "unittest"


@pytest.fixture
def echo_client(f_mqtt_credentials):
    sender = MQTTConnector(TEST_ECHO_CLIENT_NAME,
                           f_mqtt_credentials,
                           TEST_CHANNEL)
    echo = TestEchoClient(sender)
    yield echo
    sender.__del__()


@pytest.fixture
def sender(f_mqtt_credentials):
    sender = MQTTConnector(TEST_SENDER_NAME,
                           f_mqtt_credentials,
                           TEST_CHANNEL)
    yield sender
    sender.__del__()


@pytest.fixture
def manager(sender):
    manager = NetworkManager()
    manager.add_connector(sender)
    yield manager
    manager.__del__()


@pytest.mark.network
def test_mqtt_connector_send(manager: NetworkManager, f_payload_big, echo_client):
    send_test(manager, echo_client.get_hostname(), f_payload_big)


@pytest.mark.network
def test_mqtt_connector_broadcast(manager: NetworkManager, f_payload_big, echo_client):
    broadcast_test(manager, f_payload_big)


@pytest.mark.network
def test_mqtt_connector_broadcast_max_responses(manager: NetworkManager, f_payload_big, echo_client):
    broadcast_single_response_test(manager, f_payload_big)
