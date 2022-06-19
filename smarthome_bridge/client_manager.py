import logging
from typing import Optional

from smarthome_bridge.client import Client
from smarthome_bridge.status_supplier_interfaces.client_status_supplier import ClientStatusSupplier, \
    ClientAlreadyExistsError, ClientDoesntExistsError


class ClientManager(ClientStatusSupplier):
    _logger: logging.Logger
    _clients: list[Client]

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._clients = []

    def __del__(self):
        while self._clients:
            client = self._clients[0]
            self.remove_client(client.id)

    def _get_clients(self) -> list[Client]:
        return self._clients

    def add_client(self, client: Client):
        """
        Adds a client to the database and takes ownership of it

        :param client: The client to add to the database
        :return: None
        :raises ClientAlreadyExistsError: If a client with the given name is already present
        """
        self._logger.info(f"Adding client '{client.id}'")
        if self.get_client(client.id) is not None:
            raise ClientAlreadyExistsError(client.id)
        self._clients.append(client)

    def remove_client(self, client_id: str):
        """
        Removes a client from the database

        :param client_id: Name of the client that should be removed
        :return: None
        :raises ClientDoesntExistsError: If no client with the given name is present in the database
        """
        self._logger.info(f"Removing client '{client_id}'")
        client = self.get_client(client_id)
        if client is None:
            raise ClientDoesntExistsError(client_id)
        self._clients.remove(client)

    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Returns the client with the given name if present

        :param client_id: Name of the client to return
        :return: The client with the given name if present
        """
        for client in self._clients:
            if client.id == client_id:
                return client
        raise ClientDoesntExistsError(client_id)

    def get_client_ids(self) -> list[str]:
        return [x.id for x in self._clients]

    def get_client_count(self) -> int:
        """
        Gets the number of stored clients

        :return: The number of clients present
        """
        return len(self._clients)
