import pytest
import random

from smarthome_bridge.serializer import Serializer

from smarthome_bridge.smarthomeclient import SmarthomeClient
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier

# TODO: Test serialized elements with json schemas

C_NAME = "test_client"
C_RUNTIME_ID = random.randint(0, 10000)
C_FLASH_DATE = None
C_BRANCH = None
C_COMMIT = None
C_PORT_MAPPING = {}
C_BOOT_MODE = 1

CHA_TYPE = CharacteristicIdentifier.fanSpeed
CHA_MIN = 0
CHA_MAX = 100
CHA_STEPS = 4

G_NAME = "test_gadget"
G_TYPE = GadgetIdentifier.fan_westinghouse_ir
G_HOST_CLIENT = C_NAME
G_HOST_CLIENT_RUNTIME_ID = C_RUNTIME_ID


@pytest.fixture()
def serializer():
    serializer = Serializer()
    yield serializer


@pytest.fixture()
def test_client():
    client = SmarthomeClient(name=C_NAME,
                             runtime_id=C_RUNTIME_ID,
                             flash_date=C_FLASH_DATE,
                             software_commit=C_COMMIT,
                             software_branch=C_BRANCH,
                             port_mapping=C_PORT_MAPPING,
                             boot_mode=C_BOOT_MODE)
    yield client
    # client.__del__()


@pytest.fixture()
def test_characteristic():
    characteristic = Characteristic(c_type=CHA_TYPE,
                                    min_val=CHA_MIN,
                                    max_val=CHA_MAX,
                                    steps=CHA_STEPS)
    yield characteristic
    # characteristic.__del__()


@pytest.fixture()
def test_gadget(test_characteristic):
    gadget = Gadget(name=G_NAME,
                    g_type=G_TYPE,
                    host_client=G_HOST_CLIENT,
                    host_client_runtime_id=G_HOST_CLIENT_RUNTIME_ID,
                    characteristics=[test_characteristic])
    yield gadget
    gadget.__del__()


@pytest.mark.bridge
def test_serializer_client(serializer: Serializer, test_client: SmarthomeClient):
    serialized_data = serializer.serialize_client(test_client)
    assert serialized_data != {}


@pytest.mark.bridge
def test_serializer_characteristic(serializer: Serializer, test_characteristic: Characteristic):
    serialized_data = serializer.serialize_characteristic(test_characteristic)
    assert serialized_data != {}


@pytest.mark.bridge
def test_serializer_gadget(serializer: Serializer, test_gadget: Gadget):
    serialized_data = serializer.serialize_gadget(test_gadget)
    assert serialized_data != {}
