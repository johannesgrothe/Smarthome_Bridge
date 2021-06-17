import logging
from abc import ABC
from typing import Optional, Callable
import socket
import threading
import json
from jsonschema import ValidationError
from queue import Queue

# from network_connector import NetworkConnector, Request, response_callback_type, req_validation_scheme_name, Validator
from network_server import NetworkServer, NetworkServerClient, Request,\
    response_callback_type, req_validation_scheme_name, Validator, ClientDisconnectedException

_socket_server_max_clients = 10
_socket_timeout = 3
_socket_receive_len = 3000
_socket_request_scheme = "socket_request_structure"


def _format_request(req: Request) -> str:
    req_obj = {"path": req.get_path(), "body": req.get_body()}
    req_str = json.dumps(req_obj)
    return req_str


class SocketServerCreationFailedException(Exception):
    def __init__(self, host, port):
        super().__init__(f"An error occurred while binding to host '{host}' at port '{port}' ")


class SocketServerClient(NetworkServerClient):

    _socket_client: socket.socket

    def __init__(self, host_name: str, address: str, client: socket.socket):
        self._socket_client = client
        super().__init__(host_name, address)

    def __del__(self):
        super().__del__()
        self._socket_client.close()

    def _receive(self) -> Optional[Request]:
        try:
            buf_rec_data = self._socket_client.recv(_socket_receive_len).decode()
        except socket.timeout:
            return None

        if not buf_rec_data:
            return None

        try:
            buf_json = json.loads(buf_rec_data)
        except json.decoder.JSONDecodeError:
            self._logger.info(f"Could not decode JSON: '{buf_rec_data}'")
            return None

        try:
            self._validator.validate(buf_json, _socket_request_scheme)
        except ValidationError:
            self._logger.info(f"Received JSON is no valid Socket Request: '{buf_rec_data}'")
            return None

        req_body = buf_json['body']

        try:
            self._validator.validate(req_body, req_validation_scheme_name)
        except ValidationError:
            self._logger.info(f"Received JSON is no valid Request: '{req_body}'")
            return None

        buf_req = Request(buf_json["path"],
                          req_body["session_id"],
                          req_body["sender"],
                          req_body["receiver"],
                          req_body["payload"])

        return buf_req

    def send_request(self, req: Request):
        try:
            req_str = _format_request(req)
            self._socket_client.sendall(req_str.encode())
        except (ConnectionResetError, BrokenPipeError):
            raise ClientDisconnectedException


class SocketConnector(NetworkServer, ABC):

    @staticmethod
    def _receive_req_from_socket(client: socket.socket, logger: logging.Logger, validator: Validator,
                                 respond_method: Callable) -> Optional[Request]:
        try:
            buf_rec_data = client.recv(_socket_receive_len).decode()
        except socket.timeout:
            return None

        if not buf_rec_data:
            return None

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
            validator.validate(req_body, req_validation_scheme_name)
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

    @staticmethod
    def _generate_response_method(client: socket.socket, name: str) -> response_callback_type:

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

    def _create_client_handler_thread(self, client: socket.socket) -> Callable:
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


class SocketServer(SocketConnector):

    _server_socket: socket.socket
    _port: int
    _host: str

    def __init__(self, own_name: str, port: int):
        super().__init__(own_name)
        self._port = port
        self._host = socket.gethostname()

        self._start_server()

        self._thread_manager.add_thread("socket_server_accept", self._accept_new_clients)
        self._thread_manager.start_threads()

    def __del__(self):
        self._logger.info("Shutting down SocketServer")
        super().__del__()
        self._server_socket.close()

    def _start_server(self):
        self._logger.info(f"SocketServer is binding to {self._host} @ {self._port}")
        self._server_socket = socket.socket()
        self._server_socket.settimeout(_socket_timeout)
        try:
            self._server_socket.bind((self._host, self._port))
        except OSError:
            raise SocketServerCreationFailedException(self._host, self._port)

        # configure how many client the server can listen simultaneously
        self._server_socket.listen(_socket_server_max_clients)
        self._logger.info("SocketServer is listening for clients...")

    def _accept_new_clients(self):
        try:
            new_client, address = self._server_socket.accept()  # accept new connection
            if new_client:
                new_client.settimeout(_socket_timeout)
                client = SocketServerClient(self._name, str(address), new_client)
                self._add_client(client)
        except socket.timeout:
            pass


class SocketClient(SocketConnector):

    _socket_client: socket.socket
    _address: str
    _port: int

    def __init__(self, own_name: str, address: Optional[str], port: int):
        super().__init__(own_name)
        if not address or address == "localhost":
            address = socket.gethostname()
        self._port = port
        self._address = address
        self._connect()

        client_thread_method = self._create_client_handler_thread(self._socket_client)
        thread_name = f"receive_thread"
        self._thread_manager.add_thread(thread_name, client_thread_method)
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        self._disconnect()

    def _connect(self):
        self._logger.info("Starting SocketClient")
        self._socket_client = socket.socket()
        self._socket_client.settimeout(_socket_timeout)
        self._socket_client.connect((self._address, self._port))

    def _disconnect(self):
        self._logger.info("Shutting down SocketClient")
        self._socket_client.close()

    def _send_data(self, req: Request):
        req_str = _format_request(req)
        tries = 0
        while tries < 2:
            try:
                self._socket_client.send(req_str.encode())
                return
            except (ConnectionResetError, BrokenPipeError):
                self._connect()
                tries += 1
        self._logger.error("Could not send Request, connection broken")
