import logging
from abc import abstractmethod, ABCMeta

from request import Request


class Subscriber(metaclass=ABCMeta):
    @abstractmethod
    def _receive(self, req: Request):
        pass


class Publisher(metaclass=ABCMeta):

    __subscriber_clients: list
    __logger: logging.Logger

    def __init__(self):
        self.__subscriber_clients = []
        self.__logger = logging.getLogger("Publisher")

    def subscribe(self, client: Subscriber):
        self.__logger.info("Client subscribed")
        if client not in self.__subscriber_clients:
            self.__subscriber_clients.append(client)

    def unsubscribe(self, client: Subscriber):
        self.__logger.info("Client unsubscribed")
        self.__subscriber_clients.remove(client)

    def _publish(self, req: Request):
        self.__logger.debug("Publishing request")
        for subscriber in self.__subscriber_clients:
            subscriber.receive(req)
