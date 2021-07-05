import pytest
import time

from network.serial_server import SerialServer
from tests.connector_tests import send_test, send_split_test, broadcast_test,\
    broadcast_single_response_test,  test_payload_small, test_payload_big

_blocked_clients = ["/dev/tty.SLAB_USBtoUART"]
_start_delay = 2
CLIENT_NAME = "TestClient"


def dummy_fixture_usage():
    """Used to artificially 'use' fixtures to prevent them from being auto-removed"""
    s = test_payload_small()
    b = test_payload_big()


@pytest.fixture
def server():
    server = SerialServer("TestSerialServer",
                          115200)
    for client_id in _blocked_clients:
        server.block_address(client_id)
    time.sleep(_start_delay)
    yield server
    server.__del__()


def test_serial_server_send(server: SerialServer, test_payload_small: dict):
    send_test(server, CLIENT_NAME, test_payload_small)


# TODO: Check why large payloads fuck up
# def test_serial_server_send_split_long(server: SerialServer, test_payload_big: dict):
#     send_split_test(server, CLIENT_NAME, test_payload_big, part_max_len=50)


def test_serial_server_send_split_short(server: SerialServer, test_payload_small: dict):
    send_split_test(server, CLIENT_NAME, test_payload_small)


def test_serial_server_broadcast(server: SerialServer, test_payload_small):
    assert server.get_client_count() == 1
    broadcast_test(server, test_payload_small)


def test_serial_server_broadcast_max_responses(server: SerialServer, test_payload_small):
    assert server.get_client_count() == 1
    broadcast_single_response_test(server, test_payload_small)

