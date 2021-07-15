import logging

from smarthome_bridge.smarthomeclient import SmarthomeClient


class ClientManager:

    _logger: logging.Logger

    _clients: list[SmarthomeClient]

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._clients = []

    def __del__(self):
        pass

    def add_client(self, client: SmarthomeClient):
        self._clients.append(client)

    def get_client_count(self) -> int:
        return len(self._clients)
