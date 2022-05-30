from gadgets.remote.remote_gadget import RemoteGadget


class FanUpdateContainer(GadgetUpdateContainer):
    speed: bool

    def __init__(self, origin: Gadget):
        super().__init__(origin)
        self.speed = False


class Fan(RemoteGadget):
    _steps: int
    _value: int
    _update_container: FanUpdateContainer

    def __init__(self,
                 name: str,
                 host_client: str,
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
            self._update_container.speed = True

    @property
    def steps(self) -> int:
        return self._steps
