from abc import abstractmethod, ABCMeta

from gadgets.gadget import Gadget
from gadgets.remote.remote_gadget import RemoteGadget


class GadgetUpdateSubscriber(metaclass=ABCMeta):

    @abstractmethod
    def receive_gadget(self, gadget: Gadget):
        """
        Receive and handle a gadget

        :param gadget: Gadget with updated values to be handled
        :return: None
        """
        pass

    @abstractmethod
    def receive_gadget_update(self, gadget: Gadget):
        """
        Receive and handle a gadget

        :param gadget: Gadget containing the update information
        :return: None
        """
        pass


class GadgetUpdatePublisher(metaclass=ABCMeta):
    __subscriber_clients: list[GadgetUpdateSubscriber]

    def __init__(self):
        super().__init__()
        self.__subscriber_clients = []

    def subscribe(self, client: GadgetUpdateSubscriber):
        """
        Subscribes the passed client to the publisher. The client will get its `receive_update()`-method
        called if updates arise

        :param client: The client to subscribe
        :return: None
        """
        if client not in self.__subscriber_clients:
            self.__subscriber_clients.append(client)

    def unsubscribe(self, client: GadgetUpdateSubscriber):
        """
        Unsubscribes the passed client from the publisher

        :param client: The client to unsubscribe
        :return: None
        """
        self.__subscriber_clients.remove(client)

    def _publish_gadget(self, gadget: Gadget):
        """
        Publishes a new gadget for syncing purposes

        :param gadget:
        :return:
        """
        for subscriber in self.__subscriber_clients:
            subscriber.receive_gadget(gadget)

    def _publish_gadget_update(self, gadget: Gadget):
        """
        Publishes a new gadget for syncing purposes

        :param gadget: Update information to update the gadgets' status with
        :return: None
        """
        for subscriber in self.__subscriber_clients:
            subscriber.receive_gadget_update(gadget)

    @property
    def client_count(self) -> int:
        return len(self.__subscriber_clients)
