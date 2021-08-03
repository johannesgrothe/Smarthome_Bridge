import pytest
import random

from smarthome_bridge.serializer import Serializer

from smarthome_bridge.smarthomeclient import SmarthomeClient
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier

from test_helpers.gadget_fixtures import *

# TODO: Test serialized elements with json schemas

C_NAME = "test_client"
C_RUNTIME_ID = random.randint(0, 10000)
C_FLASH_DATE = None
C_BRANCH = None
C_COMMIT = None
C_PORT_MAPPING = {}
C_BOOT_MODE = 1


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


@pytest.mark.bridge
def test_serializer_client(serializer: Serializer, test_client: SmarthomeClient):
    serialized_data = serializer.serialize_client(test_client)
    assert serialized_data != {}


@pytest.mark.bridge
def test_serializer_characteristic(serializer: Serializer, f_characteristic_fan_speed: Characteristic):
    serialized_data = serializer.serialize_characteristic(f_characteristic_fan_speed)
    assert serialized_data != {}


@pytest.mark.bridge
def test_serializer_gadget(serializer: Serializer, f_any_gadget: Gadget):
    serialized_data = serializer.serialize_gadget(f_any_gadget)
    assert serialized_data != {}
