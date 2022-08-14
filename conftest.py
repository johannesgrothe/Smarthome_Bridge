import os
import datetime

from network.auth_container import CredentialsAuthContainer
from smarthome_bridge.api.api_manager import ApiManager, ApiManagerSetupContainer
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.client import Client, ClientSoftwareInformationContainer
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from system.api_definitions import ApiAccessLevel
from system.utils.software_version import SoftwareVersion
from system.utils.temp_dir_manager import TempDirManager
from test_helpers.dummy_client_controller import DummyClientController
from test_helpers.dummy_network_connector import DummyNetworkManager
from test_helpers.dummy_status_suppliers import DummyGadgetPublisherStatusSupplier, DummyBridgeStatusSupplier, \
    DummyClientStatusSupplier, DummyGadgetStatusSupplier
from test_helpers.dummy_update_manager import DummyUpdateManager
from test_helpers.network_fixtures import *

from network.mqtt_credentials_container import MqttCredentialsContainer
from utils.auth_manager import AuthManager
from utils.client_config_manager import ClientConfigManager, ConfigAlreadyExistsException
from utils.json_validator import Validator
from utils.user_manager import UserManager


def pytest_addoption(parser):
    parser.addoption("--mqtt_ip", type=str, help="IP of the mqtt broker", default=None)
    parser.addoption("--mqtt_port", type=int, help="Port of the mqtt broker", default=None)
    parser.addoption("--mqtt_username", type=str, help="Username to connect to the mqtt broker", default=None)
    parser.addoption("--mqtt_password", type=str, help="Password to connect to the mqtt broker", default=None)
    # # name = request.config.getoption("serial_client_name")


GADGET_NAME = "test_gadget"

CLIENT_NAME = "test_client"
CLIENT_RUNTIME_ID = 1776
CLIENT_CONNECTION_TIMEOUT = 3
CLIENT_FLASH_DATE = datetime.datetime(2021, 4, 25, 23, 30, 45)
CLIENT_SW_COMMIT = "f61919a3be77d28eddf63adee43c7451b31d8f49"
CLIENT_BRANCH_NAME = "develop"
CLIENT_FAULTY_PORT_MAPPING = {"1": 33, "-3": 21, "yolo": 32}
CLIENT_PORT_MAPPING = {"1": 33}
CLIENT_BOOT_MODE = 1

T_LAUNCH = datetime.datetime.now()
USER_NAME = "testadmin"
USER_PW = "testpw"
HOSTNAME = "unittest_host"


@pytest.fixture()
def f_gadget_config_broken() -> dict:
    return {
        "gadget": {
            "type": 3,
            "id": GADGET_NAME + "_2",
            "attributes": {}
        }
    }


@pytest.fixture()
def f_gadget_config() -> dict:
    return {
        "gadget": {
            "type": 0,
            "id": GADGET_NAME + "_2",
            "attributes": {
                "red": 11,
                "green": 22,
                "blue": 33
            }
        }
    }


@pytest.fixture()
def f_client_config(f_gadget_config, f_gadget_config_broken) -> dict:
    return {
        "client": {
            "runtime_id": CLIENT_RUNTIME_ID,
            "port_mapping": {},
            "boot_mode": 1,
            "software": None,
            "api_version": "1.3.7"
        },
        "gadgets": [
            f_gadget_config["gadget"],
            f_gadget_config_broken["gadget"]
        ]
    }


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
def f_config_manager(f_temp_exists) -> ClientConfigManager:
    example_config = ClientConfigManager("configs").get_config("Example")
    test_config = ClientConfigManager("configs").get_config("Example")
    test_config["name"] = "Test"
    manager = ClientConfigManager(os.path.join(f_temp_exists, "configs"))
    try:
        manager.write_config(example_config)
        manager.write_config(test_config)
    except ConfigAlreadyExistsException:
        pass
    return manager


@pytest.fixture()
def f_update_manager() -> DummyUpdateManager:
    return DummyUpdateManager()


@pytest.fixture()
def f_credentials() -> CredentialsAuthContainer:
    return CredentialsAuthContainer(USER_NAME, USER_PW)


@pytest.fixture()
def f_gadgets() -> DummyGadgetStatusSupplier:
    return DummyGadgetStatusSupplier()


@pytest.fixture()
def f_clients(f_client) -> DummyClientStatusSupplier:
    supplier = DummyClientStatusSupplier()
    supplier.add_client(f_client)
    return supplier


@pytest.fixture()
def f_bridge() -> DummyBridgeStatusSupplier:
    info = BridgeInformationContainer("dummy_bridge",
                                      "test_branch",
                                      "abcdef123456789",
                                      T_LAUNCH,
                                      "1.1.1",
                                      "2.2.2",
                                      "3.3.3",
                                      "4.4.4")
    return DummyBridgeStatusSupplier(info)


@pytest.fixture()
def f_publishers() -> GadgetPublisherStatusSupplier:
    return DummyGadgetPublisherStatusSupplier()


@pytest.fixture()
def f_auth(f_temp_exists) -> AuthManager:
    auth = AuthManager(UserManager(f_temp_exists))
    auth.users.add_user(USER_NAME, USER_PW, ApiAccessLevel.admin, persistent_user=False)
    return auth


@pytest.fixture()
def f_network() -> NetworkManager:
    manager = DummyNetworkManager(HOSTNAME)
    yield manager
    manager.__del__()


@pytest.fixture()
def f_api_manager_setup_data(f_network, f_gadgets, f_clients, f_bridge, f_publishers,
                             f_auth, f_update_manager, f_config_manager) -> ApiManagerSetupContainer:
    return ApiManagerSetupContainer(f_network,
                                    f_gadgets,
                                    f_clients,
                                    f_publishers,
                                    f_bridge,
                                    f_auth,
                                    f_update_manager,
                                    f_config_manager)


@pytest.fixture()
def f_api_manager(f_api_manager_setup_data) -> ApiManager:
    manager = ApiManager(f_api_manager_setup_data)
    DummyClientController.set_error(None)
    manager.request_handler_client._client_controller_type = DummyClientController
    yield manager
    DummyClientController.set_error(None)
    manager.__del__()


@pytest.fixture
def f_client():
    client = Client(client_id=CLIENT_NAME,
                    runtime_id=CLIENT_RUNTIME_ID,
                    software=ClientSoftwareInformationContainer(CLIENT_SW_COMMIT,
                                                                CLIENT_BRANCH_NAME,
                                                                CLIENT_FLASH_DATE),
                    port_mapping=CLIENT_FAULTY_PORT_MAPPING,
                    boot_mode=CLIENT_BOOT_MODE,
                    api_version=SoftwareVersion(1, 2, 12))
    client.set_timeout(CLIENT_CONNECTION_TIMEOUT)
    yield client


@pytest.fixture
def f_temp_exists():
    temp_dir = "temp"
    print("Creating temp dir")
    TempDirManager(temp_dir).assert_temp()
    yield temp_dir
    print("Removing temporary files")
    TempDirManager(temp_dir).clean_temp()
