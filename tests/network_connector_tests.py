# import unittest
import logging
import pytest

from network_connector import Request, NetworkReceiver
from serial_connector import SerialConnector
from mqtt_connector import MQTTConnector
from mqtt_echo_client import MQTTTestEchoClient

# Data for the MQTT Broker
BROKER_IP = "192.168.178.111"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PW = None

TEST_ECHO_CLIENT_NAME = "pytest_echo_client"
TEST_SENDER_NAME = "pytest_sender"


LOREM_IPSUM = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut " \
              "labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores " \
              "et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem " \
              "ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore " \
              "et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea " \
              "rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."

LOREM_IPSUM_SHORT = "Lorem ipsum, digga"


@pytest.fixture
def echo_client():
    echo = MQTTTestEchoClient(TEST_ECHO_CLIENT_NAME,
                              BROKER_IP,
                              BROKER_PORT,
                              BROKER_USER,
                              BROKER_PW)
    yield echo
    echo.__del__()


@pytest.fixture
def sender():
    sender = MQTTConnector(TEST_SENDER_NAME,
                           BROKER_IP,
                           BROKER_PORT,
                           BROKER_USER,
                           BROKER_PW)
    yield sender
    sender.__del__()


@pytest.fixture
def request_short():
    req = Request("smarthome/unittest",
                  None,
                  TEST_SENDER_NAME,
                  TEST_ECHO_CLIENT_NAME,
                  {"data": 12345, "lorem": LOREM_IPSUM_SHORT})
    return req


@pytest.fixture
def request_long():
    req = Request("smarthome/unittest",
                  None,
                  TEST_SENDER_NAME,
                  TEST_ECHO_CLIENT_NAME,
                  {"data": 12345, "lorem": LOREM_IPSUM})
    return req


def test_mqtt_connector_messages(sender: MQTTConnector, request_long, echo_client):

    response = sender.send_request(request_long)

    assert response is not None
    assert response.get_payload() == request_long.get_payload()
    return


def test_mqtt_connector_messages_split(sender: MQTTConnector, request_long, echo_client):

    response = sender.send_request_split(request_long)

    assert response is not None
    assert response.get_payload() == request_long.get_payload()
    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    pytest.main()
