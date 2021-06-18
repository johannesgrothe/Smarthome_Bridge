import logging
from pubsub import Subscriber
from network.request import Request
from network.network_server import NetworkServerClient
from network.network_connector import NetworkConnector


class NetworkClient(NetworkConnector, Subscriber):

    _client: NetworkServerClient
    _address: str

    def __init__(self, hostname: str, client: NetworkServerClient):
        super().__init__(hostname)
        self._hostname = hostname
        self._client = client
        self._client.subscribe(self)

    def __del__(self):
        self._client.__del__()

    def receive(self, req: Request):
        self._publish(req)

    def _send_data(self, req: Request):
        self._client.send_request(req)
