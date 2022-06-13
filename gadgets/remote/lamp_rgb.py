from typing import Tuple

from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.remote.remote_gadget import RemoteGadget


class LampRgbUpdateContainer(GadgetUpdateContainer):
    rgb: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self.rgb = False


class LampRGB(RemoteGadget):

    _red: int
    _green: int
    _blue: int
    _update_container: LampRgbUpdateContainer

    def __init__(self,
                 gadget_id: str,
                 host_client: str,
                 value_red: int = 0,
                 value_green: int = 0,
                 value_blue: int = 0):
        super().__init__(gadget_id,
                         host_client)
        self.red = value_red
        self.green = value_green
        self.blue = value_blue

    def reset_updated_properties(self):
        self._update_container = LampRgbUpdateContainer(self.id)

    @staticmethod
    def _validate_rgb_value(value: int):
        if value < 0 or value > 255:
            raise ValueError("Value needs to be between 0 and 255")

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return self.red, self.green, self.blue

    @rgb.setter
    def rgb(self, value: Tuple[int, int, int]):
        red, green, blue = value
        self.red = red
        self.green = green
        self.blue = blue

    @property
    def red(self) -> int:
        return self._red

    @red.setter
    def red(self, value: int):
        self._validate_rgb_value(value)
        if self._red != value:
            self._red = value
            self._update_container.rgb = True

    @property
    def green(self) -> int:
        return self._green

    @green.setter
    def green(self, value: int):
        self._validate_rgb_value(value)
        if self._green != value:
            self._green = value
            self._update_container.rgb = True

    @property
    def blue(self) -> int:
        return self._blue

    @blue.setter
    def blue(self, value: int):
        self._validate_rgb_value(value)
        if self._blue != value:
            self._blue = value
            self._update_container.rgb = True
