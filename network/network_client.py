import logging
from pubsub import Subscriber
from request import Request
from network_server import NetworkServerClient
from network_connector import NetworkConnector


class NetworkClient(NetworkConnector, Subscriber):

    _logger: logging.Logger
    _client: NetworkServerClient

    def __init__(self, hostname: str, client: NetworkServerClient):
        super().__init__(hostname)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._hostname = hostname
        self._client = client
        self._client.subscribe(self)

    def __del__(self):
        self._client.__del__()

    def receive(self, req: Request):
        self._publish(req)

    def _send_data(self, req: Request):
        self._client.send_request(req)
