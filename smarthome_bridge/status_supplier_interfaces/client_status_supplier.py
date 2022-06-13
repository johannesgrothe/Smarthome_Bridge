from abc import ABCMeta, abstractmethod
from typing import Optional

from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.client import Client


class ClientAlreadyExistsError(Exception):
    def __init__(self, client_name: str):
        super().__init__(f"Client '{client_name}' already exists")


class ClientDoesntExistsError(Exception):
    def __init__(self, client_name: str):
        super().__init__(f"Client '{client_name}' does not exist")


class ClientStatusSupplier(metaclass=ABCMeta):

    @abstractmethod
    @property
    def clients(self) -> list[Client]:
        """All clients stored by this status supplier"""

    @abstractmethod
    def add_client(self, client: Client) -> None:
        """
        Adds a client to the database and takes ownership of it

        :param client: The client to add to the database
        :return: None
        :raises ClientAlreadyExistsError: If a client with the given name is already present
        """

    @abstractmethod
    def remove_client(self, client_id: str) -> None:
        """
        Removes a client from the database

        :param client_id: Name of the client that should be removed
        :return: None
        :raises ClientDoesntExistsError: If no client with the given name is present in the database
        """

    @abstractmethod
    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Returns the client with the given name if present

        :param client_id: Name of the client to return
        :return: The client with the given name if present
        :raises ClientDoesntExistsError: If no client with the given name is present in the database
        """
