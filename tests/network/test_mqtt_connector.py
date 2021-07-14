import pytest

from network.mqtt_connector import MQTTConnector
from network.echo_client import TestEchoClient
from tests.network.connector_tests import send_test, send_split_test, broadcast_test, broadcast_single_response_test,\
    test_payload_small, test_payload_big

# Data for the MQTT Broker
BROKER_IP = "192.168.178.111"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PW = None

TEST_ECHO_CLIENT_NAME = "pytest_echo_client"
TEST_SENDER_NAME = "pytest_sender"


def dummy_fixture_usage():
    """Used to artificially 'use' fixtures to prevent them from being auto-removed"""
    s = test_payload_small()
    b = test_payload_big()


@pytest.fixture
def echo_client():
    sender = MQTTConnector(TEST_ECHO_CLIENT_NAME,
                           BROKER_IP,
                           BROKER_PORT,
                           BROKER_USER,
                           BROKER_PW)
    echo = TestEchoClient(sender)
    yield echo
    sender.__del__()


@pytest.fixture
def sender():
    sender = MQTTConnector(TEST_SENDER_NAME,
                           BROKER_IP,
                           BROKER_PORT,
                           BROKER_USER,
                           BROKER_PW)
    yield sender
    sender.__del__()


@pytest.mark.network
def test_mqtt_connector_send(sender: MQTTConnector, test_payload_big, echo_client):
    send_test(sender, TEST_ECHO_CLIENT_NAME, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_send_split_long(sender: MQTTConnector, test_payload_big, echo_client):
    send_split_test(sender, TEST_ECHO_CLIENT_NAME, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_send_split_short(sender: MQTTConnector, test_payload_small, echo_client):
    send_split_test(sender, TEST_ECHO_CLIENT_NAME, test_payload_small)


@pytest.mark.network
def test_mqtt_connector_broadcast(sender: MQTTConnector, test_payload_big, echo_client):
    broadcast_test(sender, test_payload_big)


@pytest.mark.network
def test_mqtt_connector_broadcast_max_responses(sender: MQTTConnector, test_payload_big, echo_client):
    broadcast_single_response_test(sender, test_payload_big)
