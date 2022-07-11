import pytest

from gadgets.classes.lamp_rgb import LampRGB, LampRgbUpdateContainer
from smarthome_bridge.api_encoders.gadgets.gadget_classes.lamp_rgb_encoder import LampRgbEncoder
from utils.json_validator import Validator


class DummyLampRGB(LampRGB):

    def __init__(self, name: str):
        super().__init__(name)
        self.mock_red = 0
        self.mock_green = 0
        self.mock_blue = 0

    def _get_red(self) -> int:
        return self.mock_red

    def _get_green(self) -> int:
        return self.mock_green

    def _get_blue(self) -> int:
        return self.mock_blue

    def _set_red(self, value: int) -> None:
        self.mock_red = value

    def _set_green(self, value: int) -> None:
        self.mock_green = value

    def _set_blue(self, value: int) -> None:
        self.mock_blue = value

    def reset_updated_properties(self):
        self._update_container = LampRgbUpdateContainer(self.id)


@pytest.fixture()
def gadget_encoder() -> LampRgbEncoder:
    return LampRgbEncoder()


@pytest.fixture()
def gadget() -> DummyLampRGB:
    return DummyLampRGB("testerinski")


@pytest.mark.bridge
def test_api_serialization_lamp_rgb(f_validator: Validator, gadget: DummyLampRGB, gadget_encoder: LampRgbEncoder):
    serialized_data = gadget_encoder.encode_gadget(gadget)
    f_validator.validate(serialized_data, "api_gadget_data")
    f_validator.validate(serialized_data["attributes"], "api_gadget_data_rgb_lamp")
