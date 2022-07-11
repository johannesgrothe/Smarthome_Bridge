import pytest
import datetime

from smarthome_bridge.api_encoders.bridge_encoder import BridgeEncoder, BridgeInformationContainer
from utils.json_validator import Validator


@pytest.fixture()
def bridge_container():
    return BridgeInformationContainer("bridge",
                                      "test_branch",
                                      "abcdef1234567890",
                                      datetime.datetime.now(),
                                      "1.2.3",
                                      "2.3.4",
                                      "3.4.5",
                                      "4.5.6")


@pytest.fixture()
def encoder():
    return BridgeEncoder()


@pytest.mark.bridge
def test_api_bridge_serialization(f_validator: Validator, encoder: BridgeEncoder,
                                  bridge_container: BridgeInformationContainer):
    serialized_data = encoder.encode_bridge_info(bridge_container)
    f_validator.validate(serialized_data, "api_get_info_response")
