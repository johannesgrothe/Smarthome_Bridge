import os

from system.exporters.temp_dir_manager import TempDirManager
from test_helpers.gadget_fixtures import *
from test_helpers.network_fixtures import *

from network.mqtt_credentials_container import MqttCredentialsContainer
from utils.json_validator import Validator
from test_helpers.dummy_gadget import DummyRemoteGadget


def pytest_addoption(parser):
    parser.addoption("--mqtt_ip", type=str, help="IP of the mqtt broker", default=None)
    parser.addoption("--mqtt_port", type=int, help="Port of the mqtt broker", default=None)
    parser.addoption("--mqtt_username", type=str, help="Username to connect to the mqtt broker", default=None)
    parser.addoption("--mqtt_password", type=str, help="Password to connect to the mqtt broker", default=None)
    # # name = request.config.getoption("serial_client_name")


@pytest.fixture()
def f_mqtt_credentials(pytestconfig, request):
    if request.config.getoption("mqtt_ip"):
        ip = request.config.getoption("mqtt_ip")
    else:
        ip = os.getenv('MQTT_IP', default=None)

    if request.config.getoption("mqtt_port"):
        port = request.config.getoption("mqtt_port")
    else:
        port = int(os.getenv('MQTT_PORT', default='1883'))

    if request.config.getoption("mqtt_username"):
        username = request.config.getoption("mqtt_username")
    else:
        username = os.getenv('MQTT_USERNAME', default=None)

    if request.config.getoption("mqtt_password"):
        password = request.config.getoption("mqtt_password")
    else:
        password = os.getenv('MQTT_PASSWORD', default=None)

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
    dummy_gadget = DummyRemoteGadget("dummy_gadget")
    yield dummy_gadget
    dummy_gadget.__del__()


@pytest.fixture
def f_temp_exists():
    temp_dir = "temp"
    print("Creating temp dir")
    TempDirManager(temp_dir).assert_temp()
    yield temp_dir
    print("Removing temporary files")
    TempDirManager(temp_dir).clean_temp()
