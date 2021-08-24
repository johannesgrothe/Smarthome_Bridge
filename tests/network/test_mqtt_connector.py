import pytest

from network.mqtt_connector import MQTTConnector
from network.mqtt_credentials_container import MqttCredentialsContainer
from network.echo_client import TestEchoClient
from tests.network.connector_tests import send_test, send_split_test, broadcast_test, broadcast_single_response_test,\
    test_payload_small, test_payload_big
from smarthome_bridge.network_manager import NetworkManager

TEST_ECHO_CLIENT_NAME = "pytest_echo_client"
TEST_SENDER_NAME = "pytest_sender"

TEST_CHANNEL = "unittest"


def dummy_fixture_usage():
    """Used to artificially 'use' fixtures to prevent them from being auto-removed"""
    s = test_payload_small()
    b = test_payload_big()


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
def test_mqtt_connector_send(manager: NetworkManager, test_payload_big, echo_client):
    send_test(manager, echo_client, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_send_split_long(manager: NetworkManager, test_payload_big, echo_client):
    send_split_test(manager, TEST_ECHO_CLIENT_NAME, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_send_split_short(manager: NetworkManager, test_payload_small, echo_client):
    send_split_test(manager, TEST_ECHO_CLIENT_NAME, test_payload_small)


@pytest.mark.network
def test_mqtt_connector_broadcast(manager: NetworkManager, test_payload_big, echo_client):
    broadcast_test(manager, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_broadcast_max_responses(manager: NetworkManager, test_payload_big, echo_client):
    broadcast_single_response_test(manager, test_payload_big)
