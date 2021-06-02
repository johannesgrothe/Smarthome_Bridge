import logging
import pytest

from mqtt_connector import MQTTConnector
from test_helpers.echo_client import TestEchoClient
from tests.connector_tests import TEST_ECHO_CLIENT_NAME, TEST_SENDER_NAME, TEST_PATH, test_payload

# Data for the MQTT Broker
BROKER_IP = "192.168.178.111"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PW = None


@pytest.fixture
def echo_client():
    sender = MQTTConnector(TEST_ECHO_CLIENT_NAME,
                           BROKER_IP,
                           BROKER_PORT,
                           BROKER_USER,
                           BROKER_PW)
    echo = TestEchoClient(TEST_ECHO_CLIENT_NAME, sender)
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


def test_mqtt_connector_send(sender: MQTTConnector, test_payload, echo_client):
    response = sender.send_request(TEST_PATH, TEST_ECHO_CLIENT_NAME, test_payload)
    assert response is not None
    assert response.get_payload() == test_payload
    return


def test_mqtt_connector_send_split(sender: MQTTConnector, test_payload, echo_client):
    response = sender.send_request_split(TEST_PATH, TEST_ECHO_CLIENT_NAME, test_payload)
    assert response is not None
    assert response.get_payload() == test_payload
    return


def test_mqtt_connector_broadcast(sender: MQTTConnector, test_payload, echo_client):
    responses = sender.send_broadcast(TEST_PATH, test_payload)
    assert len(responses) >= 1
    assert responses[0].get_payload() == test_payload
    return


def test_mqtt_connector_broadcast_max_responses(sender: MQTTConnector, test_payload, echo_client):
    responses = sender.send_broadcast(TEST_PATH, test_payload, max_responses=1)
    assert len(responses) == 1
    assert responses[0].get_payload() == test_payload
    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    pytest.main()
