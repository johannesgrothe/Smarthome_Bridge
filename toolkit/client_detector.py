"""Module for the client detector"""
import datetime
import time

from network.request import Request
from lib.pubsub import Subscriber
from smarthome_bridge.network_manager import NetworkManager


class ClientDetector(Subscriber):
    """Class to detect and protocol clients on the network"""
    _network: NetworkManager
    _clients: list[str]

    def __init__(self, network_connector: NetworkManager):
        """
        Constructor for the client detector

        :param network_connector: Network to scan for clients in
        """
        super().__init__()
        self._network = network_connector

    def __del__(self):
        self._network.unsubscribe(self)

    def receive(self, req: Request):
        if req.get_sender() not in self._clients:
            self._clients.append(req.get_sender())

    def detect_clients(self, timeout: int):
        """
        Detects clients sending messages on the network

        :param timeout: How long to scan for clients before returning
        :return: A list of all received client IDs
        """
        self._clients = []
        self._network.subscribe(self)
        time.sleep(timeout)
        self._network.unsubscribe(self)
        return self._clients
