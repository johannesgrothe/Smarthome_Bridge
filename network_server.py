import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional
from thread_manager import ThreadController

from pubsub import Publisher, Subscriber

from network_connector import NetworkConnector, Request, response_callback_type, req_validation_scheme_name, Validator
import threading


class ClientDisconnectedException(Exception):
    def __init__(self, address: str):
        super().__init__(f"Client with the Address '{address}' is disconnected")


class NetworkServerClient(Publisher):
    _host_name: str
    _address: str
    _response_method: response_callback_type
    _thread: ThreadController
    _validator: Validator
    _logger: logging.Logger

    def __init__(self, host_name: str, address: str):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._address = address
        self._validator = Validator()
        self._response_method = self._generate_response_method()

        thread_id = f"client_receiver_{address}"
        thread_method = self._create_thread_method()
        self._thread = ThreadController(thread_method, thread_id)
        self._thread.start()

    def __del__(self):
        self._thread.__del__()

    def _generate_response_method(self) -> response_callback_type:
        sender_method = self.send_request
        name = self._host_name

        def respond_to(req: Request, payload: dict, path: Optional[str] = None):
            if path:
                out_path = path
            else:
                out_path = req.get_path()

            receiver = req.get_sender()

            out_req = Request(out_path,
                              req.get_session_id(),
                              name,
                              receiver,
                              payload)

            sender_method(out_req)

        return respond_to

    def _create_thread_method(self) -> Callable:
        forward_method = self._forward_request
        receive_method = self._receive
        response_method = self._response_method

        def thread_method():
            buf_req = receive_method()
            if buf_req:
                buf_req.set_callback_method(response_method)
                forward_method(buf_req)

        return thread_method

    def _forward_request(self, req: Request):
        self._logger.info(f"Received Request at '{req.get_path()}'")
        self._publish(req)

    def get_address(self):
        return self._address

    @abstractmethod
    def send_request(self, req: Request):
        pass

    @abstractmethod
    def _receive(self) -> Optional[Request]:
        pass


class NetworkServer(NetworkConnector, Subscriber, ABC):
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
            client.subscribe(self)
        self._logger.info("New connection from: " + client.get_address())

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

    def receive(self, req: Request):
        """Used to receive Requests from ServerClients and forward them"""
        self._handle_request(req)
