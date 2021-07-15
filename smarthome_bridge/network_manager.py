import logging
from network.network_connector import NetworkConnector
from network.request import Request
from pubsub import Publisher, Subscriber


class NetworkManager(Publisher, Subscriber):

    _connectors: list[NetworkConnector]
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connectors = []

    def __del__(self):
        while self._connectors:
            client = self._connectors.pop()
            client.__del__()

    def add_connector(self, connector: NetworkConnector):
        if connector not in self._connectors:
            self._connectors.append(connector)

    def remove_connector(self, connector: NetworkConnector):
        if connector in self._connectors:
            self._connectors.remove(connector)

    def get_connector_count(self) -> int:
        return len(self._connectors)

    def receive(self, req: Request):
        self._forward_req(req)

    def _forward_req(self, req: Request):
        self._publish(req)
