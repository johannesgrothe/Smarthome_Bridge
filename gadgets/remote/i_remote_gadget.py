"""Module to contain the gadget class"""
from abc import ABC

from gadgets.remote.i_remote_gadget_update_container import IRemoteGadgetUpdateContainer
from gadgets.i_updatable_gadget import IUpdatableGadget
from smarthome_bridge.client_information_interface import ClientInformationInterface


class IRemoteGadget(IUpdatableGadget, ABC):
    _host_client: ClientInformationInterface
    _update_container: IRemoteGadgetUpdateContainer

    def __init__(self,
                 host_client: ClientInformationInterface):
        super().__init__()
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
