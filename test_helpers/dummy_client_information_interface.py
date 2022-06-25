from smarthome_bridge.client_information_interface import ClientInformationInterface


class DummyClientInformationInterface(ClientInformationInterface):
    _active: bool
    _id: str

    def __init__(self):
        self._active = True
        self._id = "test_client"

    def _is_active(self) -> bool:
        return self._active

    def _get_id(self) -> str:
        return self._id

    def set_id(self, value: str):
        self._id = value

    def set_active(self, value: bool):
        self._active = value
