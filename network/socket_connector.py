import socket
from typing import Optional

from network.network_client import NetworkClient
from network.socket_server_client import SocketServerClient, _socket_timeout


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
