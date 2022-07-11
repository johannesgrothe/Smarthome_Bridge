import pytest

from gadgets.classes.fan import Fan, FanUpdateContainer
from smarthome_bridge.api_encoders.gadgets.gadget_classes.fan_encoder import FanEncoder
from utils.json_validator import Validator


class DummyFan(Fan):

    def __init__(self, name: str):
        super().__init__(name)
        self.mock_speed = 0
        self.mock_steps = 4

    def _get_speed(self) -> int:
        return self.mock_speed

    def _set_speed(self, value: int) -> None:
        self.mock_speed = value

    def _get_steps(self) -> int:
        return self.mock_steps

    def reset_updated_properties(self):
        self._update_container = FanUpdateContainer(self.id)


@pytest.fixture()
def gadget_encoder() -> FanEncoder:
    return FanEncoder()


@pytest.fixture()
def gadget() -> DummyFan:
    return DummyFan("testerinski")


@pytest.mark.bridge
def test_api_serialization_lamp_rgb(f_validator: Validator, gadget: DummyFan, gadget_encoder: FanEncoder):
    serialized_data = gadget_encoder.encode_gadget(gadget)
    f_validator.validate(serialized_data, "api_gadget_data")
    f_validator.validate(serialized_data["attributes"], "api_gadget_data_fan")
