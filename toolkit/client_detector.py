"""Module for the client detector"""
import time

from network.request import Request
from pubsub import Subscriber
from smarthome_bridge.network_manager import NetworkManager


class ClientDetector(Subscriber):
    """Class to detect and protocol clients on the network"""
    _network: NetworkManager
    _clients: list[str]

    def __init__(self, network_connector: NetworkManager):
        super().__init__()
        self._network = network_connector
        self._network.subscribe(self)

    def receive(self, req: Request):
        if req.get_sender() not in self._clients:
            self._clients.append(req.get_sender())

    def detect_clients(self, timeout: int):
        self._clients = []
        time.sleep(timeout)
        return self._clients
