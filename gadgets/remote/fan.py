from gadgets.remote.remote_gadget import RemoteGadget


class Fan(RemoteGadget):

    _steps: int
    _value: int

    def __init__(self,
                 name: str,
                 host_client: str,
                 steps: int):
        super().__init__(name, host_client)
        if steps < 2:
            raise ValueError(f"'steps' must be at least 2")
        self._steps = steps
        self._value = 0

    def handle_attribute_update(self, attribute: str, value) -> None:
        pass

    def access_property(self, property_name: str):
        if property_name == "speed":
            return self.speed
        return super().access_property(property_name)

    @property
    def speed(self) -> int:
        return self._value

    @speed.setter
    def speed(self, value: int):
        if value < 0 or value > self._steps:
            raise ValueError(f"'value' must be between 0 and {self.steps}")
        if self.speed != value:
            self._value = value
            self._mark_attribute_for_update("speed")

    @property
    def steps(self) -> int:
        return self._steps
