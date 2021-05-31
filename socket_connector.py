from typing import Optional
import socket
import threading
import json
from jsonschema import ValidationError
from queue import Queue

from network_connector import Request, NetworkReceiver
from network_connector_threaded import ThreadedNetworkConnector

_socket_receive_len = 3000
_socket_request_scheme = "socket_request_structure"


def _format_request(req: Request) -> str:
    req_obj = {"path": req.get_path(), "body": req.get_body()}
    req_str = json.dumps(req_obj)
    return req_str


class SocketServerCreationFailedException(Exception):
    def __init__(self, host, port):
        super().__init__(f"An error occurred while binding to host '{host}' at port '{port}' ")


class SocketServer(ThreadedNetworkConnector):

    _clients: [(socket.socket, str)]
    _server_socket: socket.socket
    _port: int
    _host: str
    _lock: threading.Lock

    def __init__(self, port: int):
        super().__init__()
        self._port = port
        self._host = socket.gethostname()
        self._clients = []
        self._lock = threading.Lock()

        self._logger.info(f"SocketServer is binding to {self._host} @ {self._port}")
        self._server_socket = socket.socket()
        try:
            self._server_socket.bind((self._host, self._port))
        except OSError:
            raise SocketServerCreationFailedException(self._host, self._port)

        self._add_thread(self._accept_new_clients)

        # configure how many client the server can listen simultaneously
        self._server_socket.listen(5)
        self._logger.info("SocketServer is listening for clients...")
        self._start_threads()

    def __del__(self):
        with self._lock:
            for client, addr in self._clients:
                client.close()

    def _add_client(self, client: socket, address: str):
        with self._lock:
            self._clients.append((client, address))
        self._logger.info(f"Client '{address}' added to streaming thread")

    def _accept_new_clients(self):
        new_client, address = self._server_socket.accept()  # accept new connection
        if new_client:
            self._logger.info("New connection from: " + str(address))
            self._add_client(new_client, str(address))

    def _receive_data(self) -> Optional[Request]:
        return None

    def connected(self) -> bool:
        return True

    def _send_data(self, req: Request):
        req_str = _format_request(req)
        with self._lock:
            iterator = 0
            remove_clients: [int] = []
            for client, address in self._clients:
                try:
                    client.sendall(req_str.encode())
                except (ConnectionResetError, BrokenPipeError):
                    self._logger.info(f"Connection to '{address}' was lost")
                    # Save clients index for removal
                    remove_clients.append(iterator)
                iterator += 1

            # remove 'dead' clients
            if remove_clients:
                self._logger.info(f"Removing stored data of {len(remove_clients)} clients")
                remove_clients.reverse()
                for client_index in remove_clients:
                    self._clients.pop(client_index)


class SocketClient(ThreadedNetworkConnector):

    _request_queue: Queue

    _socket_client: socket.socket
    _address: str
    _port: int

    def __init__(self, address: str, port: int):
        super().__init__()
        self._port = port
        self._address = address
        self._connect()
        self._add_thread(self._receive_socket_data)
        self._request_queue = Queue()
        self._start_threads()

    def _connect(self):
        self._socket_client = socket.socket()
        self._socket_client.connect((self._address, self._port))

    def _send_data(self, req: Request):
        req_str = _format_request(req)
        self._socket_client.send(req_str.encode())

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

    def _receive_data(self) -> Optional[Request]:
        if self._request_queue.empty():
            return None
        buf_req = self._request_queue.get()
        return buf_req

    def connected(self) -> bool:
        return True
