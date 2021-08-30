import os

from test_helpers.gadget_fixtures import *
from network.mqtt_credentials_container import MqttCredentialsContainer
from json_validator import Validator


def pytest_addoption(parser):
    parser.addoption("--mqtt_ip", type=str, help="IP of the test-mqtt-broker")
    parser.addoption("--mqtt_port", type=int, default=1883, help="Port of the test-mqtt-broker")
    parser.addoption("--mqtt_username", type=str, help="Username of the test-mqtt-broker")
    parser.addoption("--mqtt_password", type=str, help="Password of the test-mqtt-broker")


@pytest.fixture()
def f_mqtt_credentials(pytestconfig):
    ip = os.getenv('MQTT_IP')
    port = int(os.getenv('MQTT_PORT', default='1883'))
    username = os.getenv('MQTT_USERNAME')
    password = os.getenv('MQTT_PASSWORD')
    return MqttCredentialsContainer(ip,
                                    port,
                                    username,
                                    password)


@pytest.fixture()
def f_validator():
    json_validator = Validator()
    yield json_validator
