import time
import threading
from abc import ABC

from network.network_server_client import NetworkServerClient
from thread_manager import ThreadManager
from network.network_connector import NetworkConnector

from pubsub import Subscriber, Publisher

from network.request import Request
from network.network_server_client import NetworkServerClient, ClientDisconnectedError
from logging_interface import LoggingInterface
from json_validator import Validator, ValidationError


class NetworkServer(NetworkConnector, ABC):

    _validator: Validator
    _hostname: str
    _clients: [NetworkServerClient]
    _thread_manager: ThreadManager
    __client_list_lock: threading.Lock

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self._logger.info(f"Starting {self.__class__.__name__}")
        self._clients = []
        self.__client_list_lock = threading.Lock()
        self._thread_manager = ThreadManager()
        self._thread_manager.add_thread("thread_cleanup", self.__task_cleanup_clients)

    def __del__(self):
        self._logger.info(f"Stopping {self.__class__.__name__}")
        self._thread_manager.__del__()
        while self._clients:
            client = self._clients[0]
            self._remove_client(client.get_address())

    def __task_cleanup_clients(self):
        for client in self._clients:
            if not client.is_connected():
                self._logger.info(f"Lost connection to '{client.get_address()}'")
                self._remove_client(client.get_address())
        time.sleep(1)

    def _add_client(self, client: NetworkServerClient):
        with self.__client_list_lock:
            self._clients.append(client)
            client.subscribe(self)
        self._logger.info(f"New connection from: {client.get_address()}")

    def _remove_client(self, address: str):
        client_index = 0
        with self.__client_list_lock:
            for client in self._clients:
                if address == client.get_address():
                    self._logger.info(f"Removing Client '{address}'")
                    buf_client: NetworkServerClient = self._clients.pop(client_index)
                    buf_client.__del__()
                    return
                client_index += 1

    def _send_data(self, req: Request):
        remove_clients: [str] = []

        with self.__client_list_lock:
            for client in self._clients:
                try:  # TODO: Remove if possible
                    client.send_request(req)
                except ClientDisconnectedError:
                    self._logger.info(f"Connection to '{client.get_address()}' was lost")
                    # Save clients index for removal
                    remove_clients.append(client.get_address())

        # remove 'dead' clients
        if remove_clients:
            self._logger.info(f"Removing stored data of {len(remove_clients)} clients")
            for client_address in remove_clients:
                self._remove_client(client_address)

    def get_client_count(self) -> int:
        return len(self._clients)

    def get_client_addresses(self) -> list[str]:
        addresses = []
        for client in self._clients:
            addresses.append(client.get_address())
        return addresses
