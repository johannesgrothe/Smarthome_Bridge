import os

from test_helpers.gadget_fixtures import *
from test_helpers.network_fixtures import *

from network.mqtt_credentials_container import MqttCredentialsContainer
from utils.json_validator import Validator
from test_helpers.dummy_gadget import DummyGadget


def pytest_addoption(parser):
    pass
    # parser.addoption("--serial_client_name", type=str, help="Name of the echo-test-client for the serial server test")
    # # name = request.config.getoption("serial_client_name")


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


@pytest.fixture()
def f_dummy_gadget():
    dummy_gadget = DummyGadget("dummy_gadget")
    yield dummy_gadget
    dummy_gadget.__del__()
