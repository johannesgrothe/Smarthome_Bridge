import threading
from abc import ABCMeta, abstractmethod
from typing import Optional

from gadgets.gadget import Gadget
from gadgets.local.local_gadget import LocalGadget
from gadgets.remote.remote_gadget import RemoteGadget


class GadgetStatusReceiver(metaclass=ABCMeta):
    @abstractmethod
    def receive_gadget_update(self, update_info: dict):
        """
        Receive and handle a gadget

        :param update_info: Container with the update information
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

    @abstractmethod
    def publish_gadget_update(self, gadget: Gadget):
        out_data = {
            "id": gadget.id
        }
        if "name" in gadget.updated_properties:
            out_data["name"] = gadget.name
        out_data["attributes"] = {}
        for attr in gadget.updated_properties:
            out_data["attributes"][attr] = gadget.access_property(attr)
        with self.__client_lock:
            for publisher in self.__subscriber_clients:
                publisher.receive_gadget_update(out_data)

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
