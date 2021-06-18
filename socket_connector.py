import logging
from abc import ABC
from typing import Optional, Callable
import socket
import json
from jsonschema import ValidationError
from pubsub import Publisher, Subscriber

from network.network_client import NetworkClient

from network_server import NetworkServer, NetworkServerClient, Request,\
    response_callback_type, req_validation_scheme_name, Validator, ClientDisconnectedException

_socket_server_max_clients = 10
_socket_timeout = 1
_socket_receive_len = 3000
_socket_request_scheme = "socket_request_structure"


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
        except (ConnectionResetError, BrokenPipeError):
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

    @staticmethod
    def _format_request(req: Request) -> str:
        req_obj = {"path": req.get_path(), "body": req.get_body()}
        req_str = json.dumps(req_obj)
        return req_str

    def _send(self, req: Request):
        try:
            req_str = self._format_request(req)
            self._socket_client.sendall(req_str.encode())
        except (ConnectionResetError, BrokenPipeError):
            raise ClientDisconnectedException

    def is_connected(self) -> bool:
        try:
            self._socket_client.send(".".encode())
            return True
        except (ConnectionResetError, BrokenPipeError):
            return False


class SocketServer(NetworkServer):

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
                client = SocketServerClient(self._hostname, str(address), new_client)
                self._add_client(client)
        except socket.timeout:
            pass


class SocketConnector(NetworkClient):

    _socket_client: socket.socket
    _address: str
    _port: int

    def __init__(self, hostname: str, address: Optional[str], port: int):
        if not address or address == "localhost":
            address = socket.gethostname()
        self._port = port
        self._address = address

        self._socket_client = socket.socket()
        self._socket_client.settimeout(_socket_timeout)
        self._socket_client.connect((self._address, self._port))
        buf_client = SocketServerClient(hostname, self._address, self._socket_client)

        super().__init__(hostname, buf_client)

    def __del__(self):
        super().__del__()
        self._logger.info("Shutting down SocketClient")
