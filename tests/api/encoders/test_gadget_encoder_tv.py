import pytest

from gadgets.classes.tv import TV, TvUpdateContainer
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.i_local_gadget import ILocalGadget
from gadgets.remote.i_remote_gadget import IRemoteGadget
from smarthome_bridge.api_encoders.gadgets.implementations.local_tv_encoder import TvEncoder
from smarthome_bridge.api_encoders.gadgets.local_gadget_api_encoder import LocalGadgetApiEncoderSuper
from utils.json_validator import Validator


class DummyTV(TV):

    def __init__(self, name: str):
        super().__init__(name)
        self.mock_status = False
        self.mock_source = 0
        self.mock_sources = ["test0", "test1"]

    def _get_status(self) -> bool:
        return self.mock_status

    def _set_status(self, value: bool) -> None:
        self.mock_status = value

    def _get_source(self) -> int:
        return self.mock_source

    def _set_source(self, value: int) -> None:
        self.mock_source = value

    def _get_sources(self) -> list[str]:
        return self.mock_sources

    def reset_updated_properties(self):
        self._update_container = TvUpdateContainer(self.id)


@pytest.fixture()
def gadget_encoder() -> TvEncoder:
    return TvEncoder()


@pytest.fixture()
def gadget() -> DummyTV:
    return DummyTV("testerinski")


@pytest.mark.bridge
def test_api_serialization_tv(f_validator: Validator, gadget: DummyTV, gadget_encoder: TvEncoder):
    serialized_data = gadget_encoder.encode_gadget(gadget)
    f_validator.validate(serialized_data, "api_gadget_data")
    f_validator.validate(serialized_data["attributes"], "api_gadget_data_tv")
