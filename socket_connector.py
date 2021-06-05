import logging
from typing import Optional
import socket
import threading
import json
from jsonschema import ValidationError
from queue import Queue

from network_connector import NetworkConnector, Request, response_callback_type, req_validation_scheme_name, Validator

_socket_receive_len = 3000
_socket_request_scheme = "socket_request_structure"


def _format_request(req: Request) -> str:
    req_obj = {"path": req.get_path(), "body": req.get_body()}
    req_str = json.dumps(req_obj)
    return req_str


class SocketServerCreationFailedException(Exception):
    def __init__(self, host, port):
        super().__init__(f"An error occurred while binding to host '{host}' at port '{port}' ")


class SocketServer(NetworkConnector):

    _clients: [(socket.socket, str)]
    _server_socket: socket.socket
    _port: int
    _host: str
    _lock: threading.Lock

    def __init__(self, own_name: str, port: int):
        super().__init__(own_name)
        self._port = port
        self._host = socket.gethostname()
        self._clients = []
        self._lock = threading.Lock()

        self.__id_map = {}
        self.__buf_queue = Queue()

        self._logger.info(f"SocketServer is binding to {self._host} @ {self._port}")
        self._server_socket = socket.socket()
        try:
            self._server_socket.bind((self._host, self._port))
        except OSError:
            raise SocketServerCreationFailedException(self._host, self._port)

        self._thread_manager.add_thread("socket_server_accept", self._accept_new_clients)

        # configure how many client the server can listen simultaneously
        self._server_socket.listen(5)
        self._logger.info("SocketServer is listening for clients...")
        self._thread_manager.start_threads()

    def __del__(self):
        with self._lock:
            for client, addr in self._clients:
                client.close()

    def _add_client(self, client: socket, address: str, thread_id: str):
        with self._lock:
            self._clients.append((client, address, thread_id))
        self._logger.info("New connection from: " + str(address))

    def _remove_client(self, address: str):
        client_id = 0
        with self._lock:
            for client, client_address, task_id in self._clients:
                if address == client_address:
                    self._clients.pop(client_id)
                    self._thread_manager.
                    return

    def _accept_new_clients(self):
        new_client, address = self._server_socket.accept()  # accept new connection
        if new_client:
            client_thread_method = self._create_client_handler_thread(new_client, address)
            thread_name = f"client_receiver_{address}"
            client_thread_controller = self._thread_manager.add_thread(thread_name, client_thread_method)
            client_thread_controller.start()
            self._add_client(new_client, str(address), thread_name)

    def _send_data(self, req: Request):
        req_str = _format_request(req)
        with self._lock:
            remove_clients: [str] = []
            for client, address, task_id in self._clients:
                try:
                    client.sendall(req_str.encode())
                except (ConnectionResetError, BrokenPipeError):
                    self._logger.info(f"Connection to '{address}' was lost")
                    # Save clients index for removal
                    remove_clients.append(address)

            # remove 'dead' clients
            if remove_clients:
                self._logger.info(f"Removing stored data of {len(remove_clients)} clients")
                for client_address in remove_clients:
                    self._remove_client(client_address)

    @staticmethod
    def _generate_response_method(client: socket.socket, name: str):

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

            req_str = _format_request(out_req)
            client.send(req_str.encode())

        return respond_to

    @staticmethod
    def _receive_req_from_socket(client: socket.socket, logger: logging.Logger, validator: Validator,
                                 respond_method: Callable) -> Optional[Request]:
        buf_rec_data = client.recv(_socket_receive_len).decode()

        try:
            buf_json = json.loads(buf_rec_data)
        except json.decoder.JSONDecodeError:
            logger.info(f"Could not decode JSON: '{buf_rec_data}'")
            return None

        try:
            validator.validate(buf_json, _socket_request_scheme)
        except ValidationError:
            logger.info(f"Received JSON is no valid Socket Request: '{buf_rec_data}'")
            return None

        req_body = buf_json['body']

        try:
            validator.validate(buf_json, req_validation_scheme_name)
        except ValidationError:
            logger.info(f"Received JSON is no valid Request: '{req_body}'")
            return None

        buf_req = Request(buf_json["path"],
                          req_body["session_id"],
                          req_body["sender"],
                          req_body["receiver"],
                          req_body["payload"])

        buf_req.set_callback_method(respond_method)

        return buf_req

    def _create_client_handler_thread(self, client: socket.socket, address: str) -> Thread:
        register_method = self._handle_request
        receive_method = self._receive_req_from_socket
        logger = self._logger
        validator = self._validator
        response_method = self._generate_response_method(client, self._name)

        def thread_method():
            buf_req = receive_method(client, logger, validator, response_method)
            if buf_req:
                register_method(buf_req)

        return thread_method


class SocketClient(NetworkConnector):

    _request_queue: Queue

    _socket_client: socket.socket
    _address: str
    _port: int

    def __init__(self, own_name: str, address: str, port: int):
        super().__init__(own_name)
        self._port = port
        self._address = address
        self._connect()
        self._add_thread(self._receive_socket_data)
        self._request_queue = Queue()
        self._start_threads()

    def _connect(self):
        self._socket_client = socket.socket()
        self._socket_client.connect((self._address, self._port))

    def _receive_socket_data(self):
        buf_rec_data = self._socket_client.recv(_socket_receive_len).decode()

        try:
            buf_json = json.loads(buf_rec_data)
        except json.decoder.JSONDecodeError:
            self._logger.info(f"Could not decode JSON: '{buf_rec_data}'")
            return

        try:
            self._validator.validate(buf_json, _socket_request_scheme)
        except ValidationError:
            self._logger.info(f"Received JSON is no valid Socket Request: '{buf_rec_data}'")
            return

        req_body = buf_json['body']

        try:
            self._validate_request(req_body)
        except ValidationError:
            self._logger.info(f"Received JSON is no valid Request: '{req_body}'")
            return

        buf_req = Request(buf_json["path"],
                          req_body["session_id"],
                          req_body["sender"],
                          req_body["receiver"],
                          req_body["payload"])

        self._logger.info(f"Received Socket Request at '{buf_req.get_path()}': {buf_req.get_payload()}")
        self._request_queue.put(buf_req)

    def _send_data(self, req: Request):
        req_str = _format_request(req)
        self._socket_client.send(req_str.encode())

    def _receive_data(self) -> Optional[Request]:
        if self._request_queue.empty():
            return None
        buf_req = self._request_queue.get()
        return buf_req

    def _generate_response_method(self):
        return self._respond_to

    def _get_respond_callback_for_id(self, req_id: int) -> Optional[response_callback_type]:
        return self._respond_to
