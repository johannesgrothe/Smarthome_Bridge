"""Module to contain the gadget class"""
from abc import ABC

from gadgets.gadget import Gadget
from smarthome_bridge.client_information_interface import ClientInformationInterface


class RemoteGadget(Gadget, ABC):
    _host_client: ClientInformationInterface

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
