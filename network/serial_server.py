import os

import serial

from network.network_server import NetworkServer
from network.serial_server_client import SerialServerClient


class SerialServer(NetworkServer):

    _baud_rate: int

    def __init__(self, hostname: str, baud_rate: int):
        super().__init__(hostname)
        self._baud_rate = baud_rate

        self._thread_manager.add_thread("serial_server_accept", self._accept_new_clients)
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        for client_address in self._clients:
            self._remove_client(client_address)

    @staticmethod
    def get_serial_ports() -> [str]:
        """Returns a list of all serial ports available to the system"""
        detected_ports = os.popen(f"ls /dev/tty*").read().strip("\n").split()
        valid_ports = []
        for port in detected_ports:
            if "usb" in port.lower():
                valid_ports.append(port)
        return valid_ports

    def _accept_new_clients(self):
        open_ports = [x for x in self.get_serial_ports() if x not in self.get_client_addresses()]
        for port in open_ports:
            try:
                new_client = serial.Serial(port, self._baud_rate)

                buf_client = SerialServerClient(self._hostname, port, new_client)

                self._add_client(buf_client)
            except (serial.serialutil.SerialException, OSError):
                pass
