import threading
from abc import ABCMeta, abstractmethod
from typing import Optional

from gadgets.gadget import Gadget
from gadgets.local.i_local_gadget import ILocalGadget
from gadgets.remote.i_remote_gadget import IRemoteGadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from smarthome_bridge.status_supplier_interfaces.gadget_status_receiver import GadgetStatusReceiver


class GadgetStatusSupplier(metaclass=ABCMeta):
    __subscriber_clients: list[GadgetStatusReceiver]
    __client_lock: threading.Lock

    def __init__(self):
        super().__init__()
        self.__subscriber_clients = []
        self.__client_lock = threading.Lock()

    def subscribe(self, subscriber: GadgetStatusReceiver):
        """
        Subscribes the passed client to the publisher. The client will get its `receive_update()`-method
        called if updates arise

        :param subscriber: The client to subscribe
        :return: None
        """
        with self.__client_lock:
            if subscriber not in self.__subscriber_clients:
                self.__subscriber_clients.append(subscriber)

    def unsubscribe(self, subscriber: GadgetStatusReceiver):
        """
        Unsubscribes the passed client from the publisher

        :param subscriber: The client to unsubscribe
        :return: None
        """
        with self.__client_lock:
            self.__subscriber_clients.remove(subscriber)

    def publish_gadget_update(self, container: GadgetUpdateContainer):
        with self.__client_lock:
            for publisher in self.__subscriber_clients:
                publisher.receive_gadget_update(container)

    @abstractmethod
    def get_gadget(self, gadget_id: str) -> Optional[Gadget]:
        pass

    @abstractmethod
    def add_gadget(self, gadget: Gadget):
        pass

    @abstractmethod
    def _get_gadgets(self) -> list[Gadget]:
        pass

    @property
    def gadgets(self) -> list[Gadget]:
        return self._get_gadgets()

    @property
    def local_gadgets(self) -> list[ILocalGadget]:
        return [x for x in self.gadgets if isinstance(x, ILocalGadget)]

    @property
    def remote_gadgets(self) -> list[IRemoteGadget]:
        return [x for x in self.gadgets if isinstance(x, IRemoteGadget)]
