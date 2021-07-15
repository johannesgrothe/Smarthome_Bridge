import logging

from network.request import Request
from pubsub import Subscriber

from smarthome_bridge.client_manager import ClientManager


class ApiManager(Subscriber):

    _logger: logging.Logger

    _clients: ClientManager

    def __init__(self, clients: ClientManager):
        self._clients = clients

    def __del__(self):
        pass

    def receive(self, req: Request):
        pass
