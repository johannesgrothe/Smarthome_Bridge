import pytest
import time

from smarthome_bridge.network_manager import NetworkManager
from network.socket_server import SocketServer
from network.socket_connector import SocketConnector
from test_helpers.echo_client import EchoClient
from tests.network.connector_tests import send_test, broadcast_test, \
    broadcast_single_response_test

SERVER_PORT = 5780
SERVER_IP = "localhost"

SERVER_NAME = "pytest_socket_server"
CLIENT_NAME = "pytest_socket_client"


@pytest.fixture
def server():
    server = SocketServer(SERVER_NAME,
                          SERVER_PORT)
    time.sleep(1)
    yield server
    server.__del__()


@pytest.fixture
def client(server):
    client = SocketConnector(CLIENT_NAME,
                             SERVER_IP,
                             SERVER_PORT)
    yield client
    client.__del__()


@pytest.fixture
def echo_client(client):
    echo_client = EchoClient(client)
    return echo_client


@pytest.fixture
def echo_server(server):
    echo_server = EchoClient(server)
    return echo_server


@pytest.fixture
def server_manager(server):
    manager = NetworkManager()
    manager.add_connector(server)
    yield manager
    manager.__del__()


@pytest.fixture
def client_manager(client):
    manager = NetworkManager()
    manager.add_connector(client)
    yield manager
    manager.__del__()


@pytest.mark.network
def test_socket_server_send(server_manager: NetworkManager, f_payload_big: dict, echo_client: EchoClient):
    send_test(server_manager, CLIENT_NAME, f_payload_big)


@pytest.mark.network
def test_socket_server_send_broadcast(server_manager: NetworkManager, f_payload_small: dict,
                                      echo_client: EchoClient):
    broadcast_test(server_manager, f_payload_small)


@pytest.mark.network
def test_socket_server_send_broadcast_single_resp(server_manager: NetworkManager, f_payload_small: dict,
                                                  echo_client: EchoClient):
    broadcast_single_response_test(server_manager, f_payload_small)


@pytest.mark.network
def test_socket_client_send(echo_server: EchoClient, f_payload_big: dict, client_manager: NetworkManager):
    send_test(client_manager, SERVER_NAME, f_payload_big)


@pytest.mark.network
def test_socket_client_send_broadcast(echo_server: EchoClient, f_payload_small: dict,
                                      client_manager: NetworkManager):
    broadcast_test(client_manager, f_payload_small)


@pytest.mark.network
def test_socket_client_send_broadcast_single_resp(echo_server: EchoClient, f_payload_small: dict,
                                                  client_manager: NetworkManager):
    broadcast_single_response_test(client_manager, f_payload_small)

# @pytest.mark.network
# def test_server_client_count(server: SocketServer):
#     assert server.get_client_count() == 0
#     client1 = SocketClient(CLIENT_NAME,
#                            SERVER_IP,
#                            SERVER_PORT)
#     assert server.get_client_count() == 1
#     client1.__del__()
#     assert server.get_client_count() == 0
#     client2 = SocketClient(CLIENT_NAME,
#                            SERVER_IP,
#                            SERVER_PORT)
#     assert server.get_client_count() == 1
#     client3 = SocketClient(CLIENT_NAME,
#                            SERVER_IP,
#                            SERVER_PORT)
#     assert server.get_client_count() == 2
#     client2.__del__()
#     client3.__del__()
#     assert server.get_client_count() == 0
