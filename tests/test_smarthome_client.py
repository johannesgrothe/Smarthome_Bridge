import pytest
import time
import datetime
from smarthomeclient import SmarthomeClient


CLIENT_NAME = "test_client"
RUNTIME_ID = 1776
NEW_RUNTIME_ID = 777
CONNECTION_TIMEOUT = 3

CLIENT_FLASH_DATE = datetime.datetime.now()
CLIENT_SW_COMMIT = "f61919a3be77d28eddf63adee43c7451b31d8f49"
CLIENT_BRANCH_NAME = "develop"
CLIENT_TEST_PORT_MAPPING = {"1": 33,
                            "-3": 21,
                            "yolo": 32}
CLIENT_PORT_MAPPING = {}
CLIENT_BOOT_MODE = 1


@pytest.fixture
def client():
    client = SmarthomeClient(CLIENT_NAME, RUNTIME_ID)
    client.set_timeout(CONNECTION_TIMEOUT)
    client.update_data(flash_date=CLIENT_FLASH_DATE,
                       software_commit=CLIENT_SW_COMMIT,
                       software_branch=CLIENT_BRANCH_NAME,
                       port_mapping=CLIENT_PORT_MAPPING,
                       boot_mode=CLIENT_BOOT_MODE)
    yield client


def test_smarthome_client_getters(client: SmarthomeClient):
    assert client.get_name() == CLIENT_NAME
    assert client.get_created() + datetime.timedelta(seconds=1) > datetime.datetime.now()
    assert client.get_boot_mode() == CLIENT_BOOT_MODE
    assert client.get_sw_branch() == CLIENT_BRANCH_NAME
    assert client.get_sw_commit() == CLIENT_SW_COMMIT
    assert client.get_sw_flash_time() == CLIENT_FLASH_DATE
    assert client.get_port_mapping() == {}
    assert client.serialized()


def test_smarthome_client_last_connected(client: SmarthomeClient):
    assert client.is_active() is False
    first_trigger = datetime.datetime.now()
    client.trigger_activity()
    assert client.is_active() is True
    time.sleep(CONNECTION_TIMEOUT - 0.1)
    assert client.is_active() is True
    time.sleep(0.2)
    assert client.is_active() is False

    assert first_trigger.replace(microsecond=0) == client.get_last_connected().replace(microsecond=0)


def test_smarthome_client_update(client: SmarthomeClient):
    assert client.needs_update() is False
    client.update_runtime_id(NEW_RUNTIME_ID)
    assert client.needs_update() is True


def test_smarthome_client_port_mapping(client: SmarthomeClient):
    assert client.needs_update() is False
    client.update_data(flash_date=CLIENT_FLASH_DATE,
                       software_commit=CLIENT_SW_COMMIT,
                       software_branch=CLIENT_BRANCH_NAME,
                       port_mapping=CLIENT_TEST_PORT_MAPPING,
                       boot_mode=CLIENT_BOOT_MODE)
