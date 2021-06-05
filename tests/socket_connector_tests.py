import logging
import pytest

from socket_connector import SocketServer, SocketClient
from test_helpers.echo_client import TestEchoClient
from tests.connector_tests import TEST_ECHO_CLIENT_NAME, TEST_SENDER_NAME, TEST_PATH, test_payload

# Data for the MQTT Broker
SERVER_IP = "localhost"
SERVER_PORT = 1883


@pytest.fixture
def server():
    sender = SocketServer(TEST_SENDER_NAME,
                          SERVER_PORT)
    yield sender
    sender.__del__()


@pytest.fixture
def echo_client():
    sender = SocketClient(TEST_ECHO_CLIENT_NAME,
                          SERVER_IP,
                          SERVER_PORT)
    echo = TestEchoClient(TEST_ECHO_CLIENT_NAME, sender)
    yield echo
    sender.__del__()


def test_socket_server_send(sender: SocketServer, test_payload, echo_client):
    response = sender.send_request(TEST_PATH, TEST_ECHO_CLIENT_NAME, test_payload)
    assert response is not None
    assert response.get_payload() == test_payload
    return

#
# def test_mqtt_connector_send_split(sender: MQTTConnector, test_payload, echo_client):
#     response = sender.send_request_split(TEST_PATH, TEST_ECHO_CLIENT_NAME, test_payload)
#     assert response is not None
#     assert response.get_payload() == test_payload
#     return
#
#
# def test_mqtt_connector_broadcast(sender: MQTTConnector, test_payload, echo_client):
#     responses = sender.send_broadcast(TEST_PATH, test_payload)
#     assert len(responses) >= 1
#     assert responses[0].get_payload() == test_payload
#     return
#
#
# def test_mqtt_connector_broadcast_max_responses(sender: MQTTConnector, test_payload, echo_client):
#     responses = sender.send_broadcast(TEST_PATH, test_payload, max_responses=1)
#     assert len(responses) == 1
#     assert responses[0].get_payload() == test_payload
#     return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    pytest.main()
