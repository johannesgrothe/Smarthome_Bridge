import random

from smarthome_bridge.api_encoder import ApiEncoder
from json_validator import Validator, ValidationError
from smarthome_bridge.smarthomeclient import SmarthomeClient
from gadgets.gadget import Gadget

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
def encoder():
    encoder = ApiEncoder()
    yield encoder


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
def test_api_encoder_client(f_validator: Validator, encoder: ApiEncoder, test_client: SmarthomeClient):
    serialized_data = encoder.encode_client(test_client)
    f_validator.validate(serialized_data, "api_client_data")
    assert serialized_data != {}


@pytest.mark.bridge
def test_api_encoder_characteristic(encoder: ApiEncoder, f_characteristic_fan_speed: Characteristic):
    serialized_data = encoder.encode_characteristic(f_characteristic_fan_speed)
    assert serialized_data != {}


@pytest.mark.bridge
def test_api_encoder_gadget(f_validator: Validator, encoder: ApiEncoder, f_any_gadget: Gadget):
    serialized_data = encoder.encode_gadget(f_any_gadget)
    f_validator.validate(serialized_data, "api_gadget_data")
    assert serialized_data != {}
