import logging
import os
import time

import pytest

from network.request import Request
from network.serial_server import SerialServer
from system.api_definitions import ApiURIs
from test_helpers.backtrace_detector import BacktraceDetector
from test_helpers.log_saver import LogSaver
from test_helpers.runtime_test_manager import RuntimeTestManager

SERIAL_HOSTNAME = "Client_Runtime_Test"
SERIAL_BAUDRATE = 115200
LOG_OUTPUT_FILE = os.path.join("test_reports", "client_runtime_trace.csv")
BACKTRACE_OUTPUT_FILE = os.path.join("test_reports", "client_backtraces.csv")


@pytest.fixture
def log_saver():
    log_saver = LogSaver()
    yield log_saver
    log_saver.save(LOG_OUTPUT_FILE)


@pytest.fixture
def backtrace_logger():
    backtrace_logger = BacktraceDetector()
    yield backtrace_logger
    backtrace_logger.save(BACKTRACE_OUTPUT_FILE)


@pytest.fixture
def serial(log_saver, backtrace_logger):
    server = SerialServer(SERIAL_HOSTNAME,
                          SERIAL_BAUDRATE)

    logger = logging.getLogger("Client Serial Out")

    def log_func(msg: str):
        log_saver.add_log_string(msg)
        backtrace_logger.check_line(msg)
        logger.info(msg)

    server.set_logging_callback(log_func)
    yield server
    server.__del__()


@pytest.mark.client
@pytest.mark.runtime
def test_client_runtime(serial, backtrace_logger):
    time.sleep(3)
    assert serial.get_client_count() == 1, "Either more or less than 1 Client is connected to the network"
    time.sleep(5)

    test_manager = RuntimeTestManager()

    illegal_request = Request("broken",
                              None,
                              "self",
                              None,
                              {"yolo": 3})

    sync_request = Request(ApiURIs.sync_request,
                           None,
                           "self",
                           None,
                           {})

    test_manager.add_task(0, serial.send_request, illegal_request)
    test_manager.add_task(2, serial.send_request, sync_request)

    test_manager.run(60)

    assert backtrace_logger.get_backtrace_count() == 0, f"Client crashed '{backtrace_logger.get_backtrace_count()}' times"
