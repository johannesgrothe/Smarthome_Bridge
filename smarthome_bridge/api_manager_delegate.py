from abc import ABCMeta, abstractmethod

from gadgets.gadget import Gadget
from smarthome_bridge.smarthomeclient import SmarthomeClient


class ApiManagerDelegate(metaclass=ABCMeta):

    @abstractmethod
    def handle_heartbeat(self, client_name: str, runtime_id: int):
        pass

    @abstractmethod
    def handle_gadget_update(self, gadget: Gadget):
        pass

    @abstractmethod
    def handle_client_update(self, client: SmarthomeClient):
        pass
