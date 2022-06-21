"""Module to contain the gadget class"""
from abc import ABC

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from smarthome_bridge.client_information_interface import ClientInformationInterface


class RemoteGadgetUpdateContainer(GadgetUpdateContainer):
    _client: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self._client = False

    @property
    def client(self) -> bool:
        return self._client

    def set_client(self):
        with self._lock:
            self._client = True
            self._record_change()


class RemoteGadget(Gadget, ABC):
    _host_client: ClientInformationInterface
    _update_container: RemoteGadgetUpdateContainer

    def __init__(self,
                 gadget_id: str,
                 host_client: ClientInformationInterface):
        super().__init__(gadget_id)
        self._host_client = host_client

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self.host_client == other.host_client

    @property
    def host_client(self) -> ClientInformationInterface:
        return self._host_client

    def record_client_change(self):
        self._update_container.set_client()
