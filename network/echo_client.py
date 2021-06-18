from typing import Optional

from network.network_client import NetworkClient
from pubsub import Subscriber
from request import Request
import logging


class TestEchoClient(Subscriber):

    _network: NetworkClient
    _logger: logging.Logger

    def __init__(self, network: NetworkClient):
        self._network = network
        self._logger = logging.getLogger(self.__class__.__name__)
        self._network.subscribe(self)

    def receive(self, req: Request):
        if req.get_receiver() == self._network.get_hostname():  # Normal Request
            self._logger.info(f"Received Request at '{req.get_path()}'")
        elif req.get_receiver() is None:  # Broadcast
            self._logger.info(f"Received Broadcast at '{req.get_path()}'")
        else:
            return

        req.respond(req.get_payload())

    def get_name(self):
        return self._network.get_hostname()
