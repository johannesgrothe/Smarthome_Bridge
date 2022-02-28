import logging

import pytest
import time
import os

from smarthome_bridge.network_manager import NetworkManager
from network.serial_server import SerialServer
from tests.network.connector_tests import send_test, send_split_test, broadcast_test
from toolkit.client_detector import ClientDetector

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


@pytest.fixture
def client_connected(manager: NetworkManager) -> str:
    logger = logging.getLogger("Client Setup")
    detector = ClientDetector(manager)
    clients = detector.detect_clients(5)
    assert len(clients) == 1
    client_id = clients[0]
    logger.info(f"Client Connected: {client_id}")
    return client_id


@pytest.mark.network
def test_serial_server_send(client_connected: str, manager: NetworkManager, f_payload_small: dict):
    send_test(manager, client_connected, f_payload_small)


@pytest.mark.network
def test_serial_server_broadcast(client_connected: str, manager: NetworkManager, f_payload_small: dict):
    broadcast_test(manager, f_payload_small)
