import logging
from typing import Optional

from smarthome_bridge.smarthomeclient import SmarthomeClient


class ClientAlreadyExistsError(Exception):
    def __init__(self, client_name: str):
        super().__init__(f"Client '{client_name}' already exists")


class ClientDoesntExistsError(Exception):
    def __init__(self, client_name: str):
        super().__init__(f"Client '{client_name}' does not exist")


class ClientManager:

    _logger: logging.Logger
    _clients: list[SmarthomeClient]

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._clients = []

    def __del__(self):
        while self._clients:
            client = self._clients[0]
            self.remove_client(client.get_name())

    def add_client(self, client: SmarthomeClient):
        self._logger.info(f"Adding client '{client.get_name()}'")
        if self.get_client(client.get_name()) is not None:
            raise ClientAlreadyExistsError(client.get_name())
        self._clients.append(client)

    def remove_client(self, client_id: str):
        """
        Removes a client from the database

        :param client_id: Name of the client that should be removed
        :return: None
        """
        self._logger.info(f"Removing client '{client_id}'")
        client = self.get_client(client_id)
        if client is None:
            raise ClientDoesntExistsError(client_id)
        self._clients.remove(client)
        # client.__del__()

    def _remove_client_from_remotes(self, client: SmarthomeClient):
        pass

    def get_client(self, client_id: str) -> Optional[SmarthomeClient]:
        for client in self._clients:
            if client.get_name() == client_id:
                return client
        return None

    def get_client_count(self) -> int:
        return len(self._clients)
