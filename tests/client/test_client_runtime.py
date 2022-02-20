import logging
import time

import pytest
from network.serial_server import SerialServer

SERIAL_HOSTNAME = "Client_Runtime_Test"
SERIAL_BAUDRATE = 115200


@pytest.fixture
def serial():
    server = SerialServer(SERIAL_HOSTNAME,
                          SERIAL_BAUDRATE)
    # serial.set_logging_callback(print)
    yield server
    server.__del__()


@pytest.mark.client
@pytest.mark.runtime
def test_client_runtime(serial):
    time.sleep(3)
    print(serial.get_client_count())
    assert serial.get_client_count() == 1
