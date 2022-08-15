from gadgets.classes.fan import FanUpdateContainer, Fan
from gadgets.remote.i_remote_gadget import IRemoteGadget, IRemoteGadgetUpdateContainer
from smarthome_bridge.client_information_interface import ClientInformationInterface


class RemoteFanUpdateContainer(FanUpdateContainer, IRemoteGadgetUpdateContainer):
    def __init__(self, origin: str):
        FanUpdateContainer.__init__(self, origin)
        IRemoteGadgetUpdateContainer.__init__(self)


class RemoteFan(Fan, IRemoteGadget):
    _update_container: RemoteFanUpdateContainer

    def __init__(self,
                 name: str,
                 host_client: ClientInformationInterface,
                 steps: int):
        IRemoteGadget.__init__(self, host_client)
        Fan.__init__(self, name)
        if steps < 2:
            raise ValueError(f"'steps' must be at least 2")
        self._steps = steps
        self._value = 0

    def _get_speed(self) -> int:
        return self._value

    def _set_speed(self, value: int) -> None:
        self._value = value

    def _get_steps(self) -> int:
        return self._steps

    def reset_updated_properties(self):
        self._update_container = RemoteFanUpdateContainer(self.id)
