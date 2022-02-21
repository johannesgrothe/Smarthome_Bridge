import pytest
import time
import os

from smarthome_bridge.network_manager import NetworkManager
from network.serial_server import SerialServer
from tests.network.connector_tests import send_test, send_split_test, broadcast_test


_start_delay = 2


@pytest.fixture
def server(f_blocked_serial_ports: list[str]):
    server = SerialServer("TestSerialServer",
                          115200)
    for client_id in f_blocked_serial_ports:
        server.block_address(client_id)
    time.sleep(_start_delay)
    if server.get_client_count() == 0:
        server.__del__()
        raise Exception("No client connected to serial server")
    yield server
    server.__del__()


@pytest.fixture
def manager(server):
    manager = NetworkManager()
    manager.add_connector(server)
    yield manager
    manager.__del__()


@pytest.mark.network
def test_serial_server_send(manager: NetworkManager, f_payload_small: dict):
    name = os.getenv('SERIAL_CLIENT_NAME')
    print(f"Serial client: {name}")
    assert name is not None
    send_test(manager, name, f_payload_small)


# TODO: Check why large payloads fuck up
@pytest.mark.network
def test_serial_server_send_split_long(manager: NetworkManager, f_payload_big: dict):
    name = os.getenv('SERIAL_CLIENT_NAME')
    send_split_test(manager, name, f_payload_big, part_max_len=50)


@pytest.mark.network
def test_serial_server_send_split_short(manager: NetworkManager, f_payload_small: dict):
    name = os.getenv('SERIAL_CLIENT_NAME')
    send_split_test(manager, name, f_payload_small)


@pytest.mark.network
def test_serial_server_broadcast(manager: NetworkManager, f_payload_small):
    broadcast_test(manager, f_payload_small)
