import json
import socket
from typing import Optional

from jsonschema import ValidationError

from network.network_connector import req_validation_scheme_name
from network.request import Request
from network.network_server import NetworkServerClient


_socket_timeout = 1
_socket_receive_len = 3000
_socket_request_scheme = "socket_request_structure"


class SocketServerClient(NetworkServerClient):

    _socket_client: socket.socket

    def __init__(self, host_name: str, address: str, client: socket.socket):
        super().__init__(host_name, address)
        self._socket_client = client
        self._thread_manager.start_threads()

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
                          req_body["payload"],
                          connection_type=f"Socket")

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
            return None

    def is_connected(self) -> bool:
        try:
            self._socket_client.send(".".encode())
            return True
        except (ConnectionResetError, BrokenPipeError):
            return False
