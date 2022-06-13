import threading
from abc import ABCMeta, abstractmethod
from typing import Optional

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.local.local_gadget import LocalGadget
from gadgets.remote.remote_gadget import RemoteGadget


class GadgetStatusReceiver(metaclass=ABCMeta):
    @abstractmethod
    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        """
        Receive and handle a gadget

        :param update_container: Container with the update information
        :return: None
        """
        pass

    @abstractmethod
    def add_gadget(self, gadget_id: str):
        """
        Get notified about a new gadget

        :param gadget_id: ID of the new gadget
        :return: None
        """
        pass

    @abstractmethod
    def remove_gadget(self, gadget_id: str):
        """
        Get notified about the removal of a gadget

        :param gadget_id: ID of the deleted gadget
        :return: None
        """
        pass


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
    @property
    def gadgets(self) -> list[Gadget]:
        pass

    @abstractmethod
    @property
    def local_gadgets(self) -> list[LocalGadget]:
        pass

    @abstractmethod
    @property
    def remote_gadgets(self) -> list[RemoteGadget]:
        pass
