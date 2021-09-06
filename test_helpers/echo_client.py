from network.network_connector import NetworkConnector
from pubsub import Subscriber
from network.request import Request
from logging_interface import LoggingInterface


class TestEchoClient(Subscriber, LoggingInterface):

    _network: NetworkConnector

    def __init__(self, network: NetworkConnector):
        super().__init__()
        self._network = network
        self._network.subscribe(self)

    def receive(self, req: Request):
        if req.get_receiver() == self._network.get_hostname():  # Normal Request
            self._logger.info(f"Received Request at '{req.get_path()}'")
        elif req.get_receiver() is None:  # Broadcast
            self._logger.info(f"Received Broadcast at '{req.get_path()}'")
        else:
            return

        req.respond(req.get_payload())

    def get_hostname(self):
        return self._network.get_hostname()
