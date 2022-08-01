import pytest
import time
import datetime

from conftest import CLIENT_NAME, CLIENT_BOOT_MODE, CLIENT_BRANCH_NAME, CLIENT_SW_COMMIT, CLIENT_FLASH_DATE, \
    CLIENT_PORT_MAPPING, CLIENT_RUNTIME_ID, CLIENT_CONNECTION_TIMEOUT
from smarthome_bridge.client import Client


@pytest.mark.bridge
def test_smarthome_client_getters(f_client: Client):
    assert f_client.id == CLIENT_NAME
    assert f_client.created + datetime.timedelta(seconds=1) > datetime.datetime.now()
    assert f_client.boot_mode == CLIENT_BOOT_MODE
    assert f_client.software_info.branch == CLIENT_BRANCH_NAME
    assert f_client.software_info.commit == CLIENT_SW_COMMIT
    assert f_client.software_info.date == CLIENT_FLASH_DATE
    assert f_client.get_port_mapping() == CLIENT_PORT_MAPPING
    assert f_client.runtime_id == CLIENT_RUNTIME_ID


@pytest.mark.bridge
def test_smarthome_client_last_connected(f_client: Client):
    assert f_client.is_active is False
    first_trigger = datetime.datetime.now()
    f_client.trigger_activity()
    assert f_client.is_active is True
    time.sleep(CLIENT_CONNECTION_TIMEOUT - 0.1)
    assert f_client.is_active is True
    time.sleep(0.2)
    assert f_client.is_active is False
    assert first_trigger.replace(microsecond=0) == f_client.last_connected.replace(microsecond=0)
