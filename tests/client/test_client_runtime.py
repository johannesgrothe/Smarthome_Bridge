import logging
import os

import pytest

from network.serial_server import SerialServer
from smarthome_bridge.network_manager import NetworkManager
from system.api_definitions import ApiURIs
from test_helpers.backtrace_detector import BacktraceDetector
from test_helpers.log_saver import LogSaver, LogLevel
from test_helpers.runtime_test_manager import RuntimeTestManager, TaskManagementContainer, TaskExecutionMetaCollector
from toolkit.client_detector import ClientDetector

CLIENT_NAME = "TestClient"
SERIAL_HOSTNAME = "Client_Runtime_Test"
SERIAL_BAUDRATE = 115200
LOG_OUTPUT_FILE = os.path.join("test_reports", "client_runtime_trace.csv")
BACKTRACE_OUTPUT_FILE = os.path.join("test_reports", "client_backtraces.csv")
TEST_META_OUTPUT_FILE = os.path.join("test_reports", "test_execution_meta.csv")


@pytest.fixture
def log_saver():
    log_saver = LogSaver(announced_messages=[LogLevel.error])
    yield log_saver
    log_saver.save(LOG_OUTPUT_FILE)


@pytest.fixture
def backtrace_logger():
    backtrace_logger = BacktraceDetector()
    yield backtrace_logger
    backtrace_logger.save(BACKTRACE_OUTPUT_FILE)


@pytest.fixture
def test_run_meta_collector() -> TaskExecutionMetaCollector:
    collector = TaskExecutionMetaCollector()
    yield collector
    collector.save(TEST_META_OUTPUT_FILE)


@pytest.fixture
def serial(log_saver: LogSaver, backtrace_logger: BacktraceDetector, f_blocked_serial_ports: list[str]):
    server = SerialServer(SERIAL_HOSTNAME,
                          SERIAL_BAUDRATE)
    for client_id in f_blocked_serial_ports:
        server.block_address(client_id)

    def log_func(msg: str):
        log_saver.add_log_string(msg)
        backtrace_logger.check_line(msg)

    server.set_logging_callback(log_func)
    yield server
    server.__del__()


@pytest.fixture
def network(serial: SerialServer):
    network = NetworkManager()
    network.add_connector(serial)
    network.set_default_timeout(10)
    yield network
    network.__del__()


@pytest.fixture
def client_connected(network: NetworkManager) -> str:
    logger = logging.getLogger("Client Setup")
    detector = ClientDetector(network)
    clients = detector.detect_clients(10)
    assert len(clients) == 1, "Either more or less than 1 client is connected to the network"
    client_id = clients[0]
    logger.info(f"Client Connected: {client_id}")
    return client_id


@pytest.mark.client
@pytest.mark.runtime
def test_client_runtime(network: NetworkManager, backtrace_logger: BacktraceDetector, client_connected: str,
                        test_run_meta_collector: TaskExecutionMetaCollector):
    test_manager = RuntimeTestManager(meta_collector=test_run_meta_collector)

    def task_echo():
        payload = {"test": 123123,
                   "message": "string"}
        res = network.send_request(ApiURIs.test_echo.uri,
                                   client_connected,
                                   payload)
        assert res is not None, "Received no response to echo"
        assert res.get_payload() == payload, "Echo response payload does not equal the sent one"

    def task_illegal_uri():
        payload = {"test": 555}
        network.send_request("yolokopter",
                             client_connected,
                             payload,
                             timeout=0)

    task_echo_container = TaskManagementContainer(function=task_echo,
                                                  args=[],
                                                  timeout=4,
                                                  crash_on_error=False,
                                                  task_name="Echo")
    test_manager.add_task(2, task_echo_container)

    task_illegal_uri_container = TaskManagementContainer(function=task_illegal_uri,
                                                         args=[],
                                                         timeout=10,
                                                         crash_on_error=False,
                                                         task_name="Illegal Uri")
    test_manager.add_task(0, task_illegal_uri_container)

    test_manager.run(20)

    assert backtrace_logger.get_backtrace_count() == 0, f"Client crashed" \
                                                        f"'{backtrace_logger.get_backtrace_count()}' times"
