import pytest

from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.i_local_gadget import ILocalGadget
from smarthome_bridge.api_encoders.gadgets.encoders.tv_encoder import TvEncoder
from smarthome_bridge.api_encoders.gadgets.local_gadget_api_encoder import LocalGadgetApiEncoderSuper
from utils.json_validator import Validator


@pytest.fixture()
def gadget_encoder() -> LocalGadgetApiEncoderSuper:
    return TvEncoder()


@pytest.fixture()
def local_gadget() -> ILocalGadget:
    return DenonRemoteControlGadget()



@pytest.mark.bridge
def test_api_remote_gadget_serialization(f_validator: Validator, local_gadget: ILocalGadget,
                                         gadget_encoder: LocalGadgetApiEncoderSuper):
    serialized_data = gadget_encoder.encode_gadget(local_gadget)
    f_validator.validate(serialized_data, "api_gadget_data")
