from datetime import datetime

import pytest

from smarthome_bridge.api_encoders.client_encoder import ClientApiEncoder
from smarthome_bridge.api_decoders.client_decoder import ClientDecoder
from smarthome_bridge.client import Client, ClientSoftwareInformationContainer
from system.utils.software_version import SoftwareVersion
from utils.json_validator import Validator

C_NAME = "test_client"
C_RUNTIME_ID = 133022
C_FLASH_DATE = datetime.now()
C_BRANCH = "develop"
C_COMMIT = "abcdef1234567890"
C_PORT_MAPPING = {}
C_BOOT_MODE = 1


@pytest.fixture()
def client_api_version():
    return SoftwareVersion(1, 3, 6)


@pytest.fixture()
def client_encoder():
    return ClientApiEncoder()


@pytest.fixture()
def client_decoder():
    return ClientDecoder()


@pytest.fixture()
def client_software_info():
    return ClientSoftwareInformationContainer(
        commit=C_COMMIT,
        branch=C_BRANCH,
        date=C_FLASH_DATE
    )


@pytest.fixture()
def client(client_software_info: ClientSoftwareInformationContainer, client_api_version: SoftwareVersion):
    client = Client(client_id=C_NAME,
                    runtime_id=C_RUNTIME_ID,
                    software=client_software_info,
                    port_mapping=C_PORT_MAPPING,
                    boot_mode=C_BOOT_MODE,
                    api_version=client_api_version)
    return client


@pytest.mark.bridge
def test_api_client_de_serialization(f_validator: Validator, client: Client, client_encoder: ClientApiEncoder,
                                     client_decoder: ClientDecoder):
    serialized_data = client_encoder.encode_client(client)
    f_validator.validate(serialized_data, "api_client_data")
    decoded_client = client_decoder.decode(serialized_data)
    assert decoded_client.software_info == client.software_info
    assert decoded_client == client
