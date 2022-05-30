"""Module to contain the gadget class"""
from abc import ABC, abstractmethod

from gadgets.gadget import Gadget, IllegalAttributeError


class RemoteGadget(Gadget, ABC):
    _host_client: str

    def __init__(self,
                 gadget_id: str,
                 host_client: str):
        super().__init__(gadget_id)
        self._host_client = host_client

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        return self.host_client == other.host_client

    @abstractmethod
    def access_property(self, property_name: str):
        if property_name == "host_client":
            return self.host_client
        return super().access_property(property_name)

    @property
    def host_client(self) -> str:
        return self._host_client
