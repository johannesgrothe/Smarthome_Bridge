import socket
from network.network_server import NetworkServer
from network.socket_server_client import _socket_timeout, SocketServerClient

_socket_server_max_clients = 10


class SocketServerCreationFailedException(Exception):
    def __init__(self, host, port):
        super().__init__(f"An error occurred while binding to host '{host}' at port '{port}' ")


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
        super().__del__()
        self._thread_manager.__del__()
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
