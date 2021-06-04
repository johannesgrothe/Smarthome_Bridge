from typing import Optional

from network_connector import NetworkConnector
from pubsub import Subscriber
from request import Request
import logging


class TestEchoClient(Subscriber):

    _name: str
    _network: NetworkConnector
    _logger: logging.Logger

    def __init__(self, name: str, network: NetworkConnector):
        self._name = name
        self._network = network
        self._logger = logging.getLogger(self.__class__.__name__)
        self._network.subscribe(self)

    def receive(self, req: Request):
        if req.get_receiver() == self.get_name():  # Normal Request
            self._logger.info(f"Received Request at '{req.get_path()}'")
        elif req.get_receiver() is None:  # Broadcast
            self._logger.info(f"Received Broadcast at '{req.get_path()}'")
        else:
            return

        req.respond(req.get_payload())

    def get_name(self):
        return self._name
