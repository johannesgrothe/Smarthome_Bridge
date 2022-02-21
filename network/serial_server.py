import os
from typing import Optional

import serial

from network.network_server import NetworkServer
from network.request import Request
from network.serial_server_client import SerialServerClient


class SerialServer(NetworkServer):

    _baud_rate: int
    _blocked_addresses: list[str]
    _logging_callback: Optional[callable]

    def __init__(self, hostname: str, baud_rate: int):
        super().__init__(hostname)
        self._baud_rate = baud_rate
        self._blocked_addresses = []
        self._logging_callback = None

        self._thread_manager.add_thread("serial_server_accept", self._accept_new_clients)
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()

    def set_logging_callback(self, func: Optional[callable]):
        self._logging_callback = func
        for client in self._clients:
            if isinstance(client, SerialServerClient):
                client.set_logging_callback(func)

    @staticmethod
    def get_serial_ports() -> [str]:
        """Returns a list of all serial ports available to the system"""
        detected_ports = os.popen(f"ls /dev/tty*").read().strip("\n").split()
        valid_ports = []
        for port in detected_ports:
            if "usb" in port.lower():
                valid_ports.append(port)
        return valid_ports

    def block_address(self, address: str):
        self._logger.info(f"Blocking Address '{address}'")
        if address not in self._blocked_addresses:
            self._blocked_addresses.append(address)
        self._remove_client(address)

    def unblock_address(self, address: str):
        self._logger.info(f"Unblocking Address '{address}'")
        self._blocked_addresses.remove(address)

    def _accept_new_clients(self):
        open_ports = [x for x in self.get_serial_ports()
                      if x not in self.get_client_addresses()
                      and x not in self._blocked_addresses]
        for port in open_ports:
            try:
                new_client = serial.Serial(port, self._baud_rate)
                buf_client = SerialServerClient(self._hostname, port, new_client)
                buf_client.set_logging_callback(self._logging_callback)
                self._add_client(buf_client)
            except (serial.serialutil.SerialException, OSError):
                pass
