import logging
import os

import pytest

from network.network_receiver import NetworkReceiver
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
TEST_META_PLOT_FILE = os.path.join("test_reports", "test_execution_meta.png")


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
    collector.save(TEST_META_PLOT_FILE)


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


@pytest.fixture
def task_echo_container(network: NetworkManager, client_connected: str) -> TaskManagementContainer:
    task_timeout = 4

    def task():
        payload = {"test": 123123,
                   "message": "string"}
        res = network.send_request(ApiURIs.test_echo.uri,
                                   client_connected,
                                   payload,
                                   timeout=task_timeout + 1)
        assert res is not None, "Received no response to echo"
        assert res.get_payload() == payload, "Echo response payload does not equal the sent one"

    out_container = TaskManagementContainer(function=task,
                                            args=[],
                                            timeout=task_timeout,
                                            crash_on_error=False,
                                            task_name="Echo")
    return out_container


@pytest.fixture
def task_illegal_uri_container(network: NetworkManager, client_connected: str) -> TaskManagementContainer:
    def task():
        payload = {"test": 555}
        network.send_request("yolokopter",
                             client_connected,
                             payload,
                             timeout=0)

    out_container = TaskManagementContainer(function=task,
                                            args=[],
                                            timeout=2,
                                            crash_on_error=False,
                                            task_name="Illegal URI")
    return out_container


@pytest.fixture
def task_sync_container(network: NetworkManager, client_connected: str) -> TaskManagementContainer:
    task_timeout = 7

    def task():
        receiver = NetworkReceiver()
        network.subscribe(receiver)
        receiver.start_listening()

        network.send_request(ApiURIs.sync_request.uri,
                             client_connected,
                             {},
                             timeout=task_timeout + 1)

        reqs = receiver.collect_requests()
        network.unsubscribe(receiver)
        sync_reqs = [x for x in reqs if x.get_sender() == client_connected and x.get_path() == ApiURIs.sync_client.uri]
        assert len(sync_reqs) == 1

    out_container = TaskManagementContainer(function=task,
                                            args=[],
                                            timeout=task_timeout,
                                            crash_on_error=False,
                                            task_name="Sync")
    return out_container


@pytest.mark.client
@pytest.mark.runtime
def test_client_runtime(backtrace_logger: BacktraceDetector, test_run_meta_collector: TaskExecutionMetaCollector,
                        task_echo_container, task_illegal_uri_container, task_sync_container):
    test_manager = RuntimeTestManager(meta_collector=test_run_meta_collector)

    test_manager.add_task(0, task_illegal_uri_container)
    test_manager.add_task(2, task_echo_container)
    test_manager.add_task(3, task_sync_container)

    test_manager.run(300)

    assert backtrace_logger.get_backtrace_count() == 0, f"Client crashed" \
                                                        f"'{backtrace_logger.get_backtrace_count()}' times"
