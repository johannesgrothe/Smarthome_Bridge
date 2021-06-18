import logging
from abc import ABC, abstractmethod
from typing import Optional
from thread_manager import ThreadManager
from queue import Queue

from pubsub import Publisher, Subscriber

from network.network_connector import NetworkConnector, Request, response_callback_type, Validator
from network.split_request_handler import SplitRequestHandler
import threading


class ClientDisconnectedException(Exception):
    def __init__(self, address: str):
        super().__init__(f"Client with the Address '{address}' is disconnected")


class NetworkServerClient(Publisher):
    _host_name: str
    _address: str
    _response_method: response_callback_type
    _validator: Validator
    _logger: logging.Logger

    _thread_manager: ThreadManager

    __split_handler: SplitRequestHandler

    __out_queue: Queue
    __in_queue: Queue

    def __init__(self, host_name: str, address: str):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._address = address
        self._validator = Validator()

        self.__split_handler = SplitRequestHandler()

        self.__out_queue = Queue()
        self.__in_queue = Queue()

        self._thread_manager = ThreadManager()
        self._thread_manager.add_thread("send_thread", self.__task_send)
        self._thread_manager.add_thread("receive_thread", self.__task_receive)
        self._thread_manager.start_threads()

    def __task_send(self):
        if not self.__out_queue.empty():
            out_req = self.__out_queue.get()
            self._send(out_req)

    def __task_receive(self):
        in_req = self._receive()
        if in_req:
            req = self.__split_handler.handle(in_req)
            if req:
                req.set_callback_method(self._respond_to)
                self._publish(req)

    def __del__(self):
        self._thread_manager.__del__()

    def _respond_to(self, req: Request, payload: dict, path: Optional[str] = None):
        if path:
            out_path = path
        else:
            out_path = req.get_path()

        receiver = req.get_sender()

        out_req = Request(out_path,
                          req.get_session_id(),
                          self._host_name,
                          receiver,
                          payload)

        self._send(out_req)

    def _forward_request(self, req: Request):
        self._logger.info(f"Received Request at '{req.get_path()}'")
        self._publish(req)

    def get_address(self):
        return self._address

    def send_request(self, req: Request):
        self.__out_queue.put(req)

    @abstractmethod
    def _send(self, req: Request):
        pass

    @abstractmethod
    def _receive(self) -> Optional[Request]:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass


class NetworkServer(NetworkConnector, Subscriber, ABC):
    _clients: [NetworkServerClient]
    _thread_manager: ThreadManager
    __lock: threading.Lock

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self._clients = []
        self.__lock = threading.Lock()
        self._thread_manager = ThreadManager()

    def __del__(self):
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
