from toolkit.client_controller import ClientController
from toolkit.client_detector import ClientDetector
from toolkit.direct_connection_toolkit import DirectConnectionToolkit
from toolkit.toolkit_meta import TOOLKIT_NETWORK_NAME
from network.serial_server import SerialServer
from smarthome_bridge.network_manager import NetworkManager
import time

_blocked_clients = ["/dev/tty.SLAB_USBtoUART"]


class DirectSerialConnectionToolkit(DirectConnectionToolkit):
    _network: NetworkManager
    _network: SerialServer

    def __init__(self):
        super().__init__()
        connector = SerialServer(TOOLKIT_NETWORK_NAME,
                                 115200)
        for client_id in _blocked_clients:
            connector.block_address(client_id)
        self._network.add_connector(connector)

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        pass

    def _scan_for_clients(self) -> [str]:
        time.sleep(7)
        return ClientDetector(self._network).detect_clients(3)
