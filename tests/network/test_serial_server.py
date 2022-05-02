import pytest
import time
import os

from smarthome_bridge.network_manager import NetworkManager
from network.serial_server import SerialServer
from tests.network.connector_tests import send_test, send_split_test, broadcast_test

_blocked_clients = ["/dev/tty.SLAB_USBtoUART"]
_start_delay = 2


@pytest.fixture
def server():
    server = SerialServer("TestSerialServer",
                          115200)
    for client_id in _blocked_clients:
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


@pytest.mark.network
def test_serial_server_broadcast(manager: NetworkManager, f_payload_small):
    broadcast_test(manager, f_payload_small)
