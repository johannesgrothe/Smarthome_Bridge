from abc import ABC, abstractmethod
from typing import Tuple

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer


class LampRgbUpdateContainer(GadgetUpdateContainer):
    _rgb: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self._rgb = False

    @property
    def rgb(self) -> bool:
        return self._rgb

    def set_rgb(self):
        with self.__lock:
            self._rgb = True
            self._record_change()


class LampRGB(Gadget, ABC):
    _update_container: LampRgbUpdateContainer

    def __init__(self,
                 gadget_id: str):
        Gadget.__init__(self, gadget_id)
        # super().__init__(gadget_id)

    @abstractmethod
    def _get_red(self) -> int:
        pass

    @abstractmethod
    def _get_green(self) -> int:
        pass

    @abstractmethod
    def _get_blue(self) -> int:
        pass

    @abstractmethod
    def _set_red(self, value: int) -> None:
        pass

    @abstractmethod
    def _set_green(self, value: int) -> None:
        pass

    @abstractmethod
    def _set_blue(self, value: int) -> None:
        pass

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
        return self._get_red()

    @red.setter
    def red(self, value: int):
        self._validate_rgb_value(value)
        if self._get_red() != value:
            self._set_red(value)
            self._update_container.set_rgb()

    @property
    def green(self) -> int:
        return self._get_green()

    @green.setter
    def green(self, value: int):
        self._validate_rgb_value(value)
        if self._get_green() != value:
            self._set_green(value)
            self._update_container.set_rgb()

    @property
    def blue(self) -> int:
        return self._get_blue()

    @blue.setter
    def blue(self, value: int):
        self._validate_rgb_value(value)
        if self._get_blue() != value:
            self._set_blue(value)
            self._update_container.set_rgb()
