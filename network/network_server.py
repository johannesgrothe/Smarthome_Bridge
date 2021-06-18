import logging
from abc import ABC, abstractmethod
from typing import Optional

from network.network_server_client import NetworkServerClient, ClientDisconnectedException
from thread_manager import ThreadManager
from queue import Queue

from pubsub import Publisher, Subscriber

from network.network_connector import NetworkConnector, Request, response_callback_type, Validator
from network.split_request_handler import SplitRequestHandler
import threading


class NetworkServer(NetworkConnector, Subscriber, ABC):
    _clients: [NetworkServerClient]
    _thread_manager: ThreadManager
    __lock: threading.Lock

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self._logger.info(f"Starting {self.__class__.__name__}")
        self._clients = []
        self.__lock = threading.Lock()
        self._thread_manager = ThreadManager()

    def __del__(self):
        self._logger.info(f"Stopping {self.__class__.__name__}")
        super().__del__()
        while self._clients:
            client = self._clients[0]
            self._remove_client(client.get_address())

    def _add_client(self, client: NetworkServerClient):
        with self.__lock:
            self._clients.append(client)
            client.subscribe(self)
        self._logger.info(f"New connection from: {client.get_address()}")

    def _remove_client(self, address: str):
        client_index = 0
        self._logger.info(f"Removing Client '{address}'")
        with self.__lock:
            for client in self._clients:
                if address == client.get_address():
                    buf_client: NetworkServerClient = self._clients.pop(client_index)
                    buf_client.__del__()
                    return
                client_index += 1

    def _send_data(self, req: Request):
        remove_clients: [str] = []

        with self.__lock:
            for client in self._clients:
                try:
                    client.send_request(req)
                except ClientDisconnectedException:
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
