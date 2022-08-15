from abc import ABC, abstractmethod

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer


class FanUpdateContainer(GadgetUpdateContainer):
    _speed: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self._speed = False

    @property
    def speed(self) -> bool:
        with self.__lock:
            return self._speed

    def set_speed(self):
        with self.__lock:
            self._speed = True
            self._record_change()


class Fan(Gadget, ABC):
    _update_container: FanUpdateContainer

    def __init__(self,
                 name: str):
        super().__init__(name)

    @abstractmethod
    def _get_speed(self) -> int:
        pass

    @abstractmethod
    def _set_speed(self, value: int) -> None:
        pass

    @abstractmethod
    def _get_steps(self) -> int:
        pass

    @property
    def speed(self) -> int:
        return self._get_speed()

    @speed.setter
    def speed(self, value: int):
        if value < 0 or value > self._get_steps():
            raise ValueError(f"'value' must be between 0 and {self._get_steps()}")
        if self._get_speed() != value:
            self._set_speed(value)
            self._update_container.set_speed()

    @property
    def steps(self) -> int:
        return self._get_steps()
