import pytest
import time

from network.serial_server import SerialServer
from tests.connector_tests import broadcast_test, broadcast_single_response_test,  test_payload_small, test_payload_big

_blocked_clients = ["/dev/tty.SLAB_USBtoUART"]
_start_delay = 2


def dummy_fixture_usage():
    """Used to artificially 'use' fixtures to prevent them from being auto-removed"""
    s = test_payload_small()


@pytest.fixture
def server():
    server = SerialServer("TestSerialServer",
                          115200)
    for client_id in _blocked_clients:
        server.block_address(client_id)
    time.sleep(_start_delay)
    yield server
    server.__del__()


def test_serial_server_broadcast(server: SerialServer, test_payload_small):
    assert server.get_client_count() == 1
    broadcast_test(server, test_payload_small)


def test_serial_server_broadcast_max_responses(server: SerialServer, test_payload_small):
    assert server.get_client_count() == 1
    broadcast_single_response_test(server, test_payload_small)
