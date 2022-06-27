import pytest

from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from gadgets.remote.i_remote_gadget import IRemoteGadget
from smarthome_bridge.api_decoders.remote_gadget_decoder import RemoteGadgetDecoder
from smarthome_bridge.api_encoders.gadgets.encoders.lamp_rgb_encoder import LampRgbEncoder
from smarthome_bridge.api_encoders.gadgets.remote_gadget_api_encoder import RemoteGadgetApiEncoderSuper
from system.gadget_definitions import RemoteGadgetIdentifier
from test_helpers.dummy_client_information_interface import DummyClientInformationInterface
from utils.json_validator import Validator


@pytest.fixture()
def gadget_encoder() -> RemoteGadgetApiEncoderSuper:
    return LampRgbEncoder()


@pytest.fixture()
def gadget_decoder() -> RemoteGadgetDecoder:
    return RemoteGadgetDecoder()


@pytest.fixture()
def dummy_interface() -> DummyClientInformationInterface:
    return DummyClientInformationInterface()


@pytest.fixture()
def remote_gadget(dummy_interface: DummyClientInformationInterface) -> IRemoteGadget:
    return RemoteLampRGB("test_gadget",
                         dummy_interface,
                         12,
                         33,
                         166)


@pytest.fixture()
def remote_gadget_data() -> dict:
    return {
        "id": "test_gadget",
        "type": RemoteGadgetIdentifier.lamp_neopixel_rgb_basic.value,
        "attributes": {
            "red": 12,
            "green": 33,
            "blue": 166
        }
    }


@pytest.mark.bridge
def test_api_remote_gadget_serialization(f_validator: Validator, remote_gadget: IRemoteGadget,
                                         gadget_encoder: RemoteGadgetApiEncoderSuper):
    serialized_data = gadget_encoder.encode_gadget(remote_gadget)
    f_validator.validate(serialized_data, "api_gadget_data")


@pytest.mark.bridge
def test_api_remote_gadget_deserialization(f_validator: Validator, remote_gadget: IRemoteGadget,
                                           remote_gadget_data: dict,
                                           gadget_decoder: RemoteGadgetDecoder):
    f_validator.validate(remote_gadget_data, "api_gadget_sync_data")
    deserialized_gadget = gadget_decoder.decode(remote_gadget_data, remote_gadget.host_client)
    assert remote_gadget == deserialized_gadget
