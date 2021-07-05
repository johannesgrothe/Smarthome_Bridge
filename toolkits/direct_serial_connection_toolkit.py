from toolkits.direct_connection_toolkit import DirectConnectionToolkit
from toolkits.toolkit_meta import TOOLKIT_NETWORK_NAME
from network.serial_server import SerialServer
from network.network_server import NetworkServer
import time


class DirectSerialConnectionToolkit(DirectConnectionToolkit):

    _network: NetworkServer

    def __init__(self):
        super().__init__()
        self._network = SerialServer(TOOLKIT_NETWORK_NAME,
                                     115200)

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        pass

    def _scan_for_clients(self) -> [str]:
        print("Waiting for clients to connect...")
        time.sleep(5)
        return self._network.get_client_addresses()
