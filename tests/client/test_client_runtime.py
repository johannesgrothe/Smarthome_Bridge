import logging
import os
import time

import pytest
from network.serial_server import SerialServer
from test_helpers.backtrace_detector import BacktraceDetector
from test_helpers.log_saver import LogSaver

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

    def log_func(msg: str):
        log_saver.add_log_string(msg)
        backtrace_logger.check_line(msg)

    server.set_logging_callback(log_func)
    yield server
    server.__del__()


@pytest.mark.client
@pytest.mark.runtime
def test_client_runtime(serial, backtrace_logger):
    time.sleep(3)
    assert serial.get_client_count() == 1
    time.sleep(30)
    assert backtrace_logger.get_backtrace_count() == 0
