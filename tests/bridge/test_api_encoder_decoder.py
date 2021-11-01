import random
from datetime import datetime

from smarthome_bridge.api_encoder import ApiEncoder, GadgetEncodeError, IdentifierEncodeError
from smarthome_bridge.api_decoder import ApiDecoder, ClientDecodeError, GadgetDecodeError, CharacteristicDecodeError

from json_validator import Validator, ValidationError
from smarthome_bridge.client import Client
from gadgets.gadget import Gadget, GadgetIdentifier

from test_helpers.gadget_fixtures import *

# TODO: Test serialized elements with json schemas

C_NAME = "test_client"
C_RUNTIME_ID = random.randint(0, 10000)
C_FLASH_DATE = datetime.now()
C_BRANCH = "develop"
C_COMMIT = None
C_PORT_MAPPING = {}
C_BOOT_MODE = 1


@pytest.fixture()
def encoder():
    encoder = ApiEncoder()
    yield encoder


@pytest.fixture()
def decoder():
    decoder = ApiDecoder()
    yield decoder


@pytest.fixture()
def test_client():
    client = Client(name=C_NAME,
                    runtime_id=C_RUNTIME_ID,
                    flash_date=C_FLASH_DATE,
                    software_commit=C_COMMIT,
                    software_branch=C_BRANCH,
                    port_mapping=C_PORT_MAPPING,
                    boot_mode=C_BOOT_MODE)
    yield client
    # client.__del__()


@pytest.mark.bridge
def test_api_client_de_serialization(f_validator: Validator, encoder: ApiEncoder, decoder: ApiDecoder,
                                     test_client: Client):
    serialized_data = encoder.encode_client(test_client)
    f_validator.validate(serialized_data, "api_client_data")
    decoded_client = decoder.decode_client(serialized_data, test_client.get_name())
    assert decoded_client == test_client


@pytest.mark.bridge
def test_api_characteristic_de_serialization(encoder: ApiEncoder, decoder: ApiDecoder,
                                             f_characteristic_fan_speed: Characteristic):
    f_characteristic_fan_speed.set_step_value(2)
    serialized_data = encoder.encode_characteristic(f_characteristic_fan_speed)
    deserialized_characteristic = decoder.decode_characteristic(serialized_data)
    assert deserialized_characteristic == f_characteristic_fan_speed
    assert deserialized_characteristic.get_step_value() == f_characteristic_fan_speed.get_step_value()


@pytest.mark.bridge
def test_api_gadget_de_serialization(f_validator: Validator, encoder: ApiEncoder, decoder: ApiDecoder,
                                     f_any_gadget: Gadget, f_dummy_gadget: Gadget):
    serialized_data = encoder.encode_gadget(f_any_gadget)
    f_validator.validate(serialized_data, "api_gadget_data")

    with pytest.raises(NotImplementedError):
        deserialized_gadget = decoder.decode_gadget(serialized_data, f_any_gadget.get_host_client())
    # assert deserialized_gadget.equals(f_any_gadget)

    with pytest.raises(GadgetEncodeError):
        encoder.encode_gadget(f_dummy_gadget)


@pytest.mark.bridge
def test_api_gadget_identifier_de_serialization(encoder: ApiEncoder, f_any_gadget: Gadget, f_dummy_gadget: Gadget):
    identifier = encoder.encode_gadget_identifier(f_any_gadget)
    assert identifier == GadgetIdentifier.any_gadget

    with pytest.raises(IdentifierEncodeError):
        encoder.encode_gadget_identifier(f_dummy_gadget)
