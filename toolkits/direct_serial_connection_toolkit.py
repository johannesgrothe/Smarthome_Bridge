from toolkits.direct_connection_toolkit import DirectConnectionToolkit
from toolkits.toolkit_meta import TOOLKIT_NETWORK_NAME
from network.serial_server import SerialServer
from network.network_server import NetworkServer
import time

_blocked_clients = ["/dev/tty.SLAB_USBtoUART"]


class DirectSerialConnectionToolkit(DirectConnectionToolkit):

    _network: NetworkServer
    _network: SerialServer

    def __init__(self):
        super().__init__()
        self._network = SerialServer(TOOLKIT_NETWORK_NAME,
                                     115200)
        for client_id in _blocked_clients:
            self._network.block_address(client_id)

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        pass

    def _scan_for_clients(self) -> [str]:
        time.sleep(7)
        responses = self._network.send_broadcast("smarthome/broadcast/req", {}, timeout=6)
        client_names = [res.get_sender() for res in responses]
        return client_names
