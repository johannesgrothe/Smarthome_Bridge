from abc import ABC, abstractmethod
from typing import Callable
from thread_manager import ThreadController

from network_connector import NetworkConnector, Request, response_callback_type, req_validation_scheme_name, Validator
import threading


class ClientDisconnectedException(Exception):
    def __init__(self, address: str):
        super().__init__(f"Client with the Address '{address}' is disconnected")


class NetworkServerClient:
    _address: str
    _thread_id: str
    _thread_method: Callable
    _thread: ThreadController

    def __init__(self, address: str, thread_method: Callable):
        self._address = address
        self._thread_id = f"client_receiver_{address}"
        self._thread_method = thread_method
        self._thread = ThreadController(self._thread_method, self._thread_id)
        self._thread.start()

    def __del__(self):
        self._thread.__del__()

    def get_address(self):
        return self._address

    def get_thread_method(self):
        return self._thread_method

    @abstractmethod
    def send_request(self, req: Request):
        pass


class NetworkServer(NetworkConnector, ABC):
    _clients: [NetworkServerClient]
    __lock: threading.Lock

    def __init__(self, name: str):
        super().__init__(name)
        self._clients = []
        self.__lock = threading.Lock()

    def __del__(self):
        super().__del__()
        while self._clients:
            client = self._clients[0]
            self._remove_client(client.get_address())

    def _add_client(self, client: NetworkServerClient):
        with self.__lock:
            self._clients.append(client)
        self._logger.info("New connection from: " + client.get_address())

    def _remove_client(self, address: str):
        client_index = 0
        self._logger.info(f"Removing Client '{address}'")
        with self.__lock:
            for client in self._clients:
                if address == client.get_address():
                    self._clients.pop(client_index)
                    return
                client_index += 1

    def _send_data(self, req: Request):
        with self.__lock:
            remove_clients: [str] = []
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
