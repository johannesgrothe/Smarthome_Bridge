from gadgets.classes.lamp_rgb import LampRGB, LampRgbUpdateContainer
from gadgets.remote.i_remote_gadget import IRemoteGadget, IRemoteGadgetUpdateContainer
from smarthome_bridge.client_information_interface import ClientInformationInterface


class RemoteLampRgbUpdateContainer(LampRgbUpdateContainer, IRemoteGadgetUpdateContainer):
    def __init__(self, origin: str):
        LampRgbUpdateContainer.__init__(self, origin)
        IRemoteGadgetUpdateContainer.__init__(self)


class RemoteLampRGB(LampRGB, IRemoteGadget):
    _red: int
    _green: int
    _blue: int
    _update_container: RemoteLampRgbUpdateContainer

    def __init__(self,
                 gadget_id: str,
                 host_client: ClientInformationInterface,
                 value_red: int = 0,
                 value_green: int = 0,
                 value_blue: int = 0):
        IRemoteGadget.__init__(self, host_client)
        LampRGB.__init__(self, gadget_id)
        self._red = value_red
        self._green = value_green
        self._blue = value_blue

    def reset_updated_properties(self):
        self._update_container = RemoteLampRgbUpdateContainer(self.id)

    def _get_red(self) -> int:
        return self._red

    def _get_green(self) -> int:
        return self._green

    def _get_blue(self) -> int:
        return self._blue

    def _set_red(self, value: int) -> None:
        self._red = value

    def _set_green(self, value: int) -> None:
        self._green = value

    def _set_blue(self, value: int) -> None:
        self._blue = value
