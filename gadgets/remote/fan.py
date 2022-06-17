from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.remote.remote_gadget import RemoteGadget
from smarthome_bridge.client_information_interface import ClientInformationInterface


class FanUpdateContainer(GadgetUpdateContainer):
    _speed: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self._speed = False

    @property
    def speed(self) -> bool:
        with self._lock:
            return self._speed

    def set_speed(self):
        with self._lock:
            self._speed = True
            self._record_change()


class Fan(RemoteGadget):
    _steps: int
    _value: int
    _update_container: FanUpdateContainer

    def __init__(self,
                 name: str,
                 host_client: ClientInformationInterface,
                 steps: int):
        super().__init__(name, host_client)
        if steps < 2:
            raise ValueError(f"'steps' must be at least 2")
        self._steps = steps
        self._value = 0

    def reset_updated_properties(self):
        self._update_container = FanUpdateContainer(self.id)

    @property
    def speed(self) -> int:
        return self._value

    @speed.setter
    def speed(self, value: int):
        if value < 0 or value > self._steps:
            raise ValueError(f"'value' must be between 0 and {self.steps}")
        if self.speed != value:
            self._value = value
            self._update_container.set_speed()

    @property
    def steps(self) -> int:
        return self._steps
