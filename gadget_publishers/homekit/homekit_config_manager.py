import json
import random
import socket
from typing import Optional

from lib.logging_interface import LoggingInterface


class NoConfigFoundError(Exception):
    pass


class HomekitConfigManager(LoggingInterface):
    _config_path: str
    _data: Optional[dict]

    def __init__(self, config_path: str):
        super().__init__()
        self._config_path = config_path
        self._reload()

    def _reload(self):
        try:
            with open(self._config_path, "r") as file_p:
                self._data = json.load(file_p)
        except FileNotFoundError:
            self._data = None

    @property
    def path(self) -> str:
        return self._config_path

    @property
    def data(self) -> dict:
        return self._data

    @staticmethod
    def _generate_host_ip() -> str:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    @staticmethod
    def _generate_pin() -> str:
        d = [random.randint(0, 9) for _ in range(8)]
        return f"{d[0]}{d[1]}{d[2]}-{d[3]}{d[4]}-{d[5]}{d[6]}{d[7]}"

    @staticmethod
    def _generate_pairing_id_part() -> str:
        hex_val = hex(random.randint(0, 255))
        shorted = hex_val[2:].upper()
        if len(shorted) == 1:
            shorted = "0" + shorted
        return shorted

    @classmethod
    def _generate_pairing_id(cls) -> str:
        id_bytes = [cls._generate_pairing_id_part() for _ in range(6)]
        return ":".join(id_bytes)

    def generate_new_config(self) -> None:
        """
        Generates an all new config and replaces any old one (including all pairing information)

        :return: None
        """
        self._logger.info("Creating new config file")
        new_config = {
            "accessory_pairing_id": self._generate_pairing_id(),
            "accessory_pin": self._generate_pin(),
            "c#": 0,
            "category": "Bridge",
            "host_ip": self._generate_host_ip(),
            "host_port": 9890,
            "name": "Python_Smarthome_Bridge"
        }

        with open(self._config_path, "w") as file_p:
            json.dump(new_config, file_p)
        self._reload()

    def reset_config_pairings(self) -> None:
        """
        Removes all pairing information from config

        :return: None
        """
        try:
            with open(self._config_path, "r") as file_p:
                cfg_data = json.load(file_p)
        except FileNotFoundError:
            raise NoConfigFoundError(f"No file found at path '{self._config_path}'")

        needed_keys = ["accessory_pairing_id", "accessory_pin",
                       "c#", "category", "host_ip", "host_port",
                       "name"]

        try:
            new_config = {
                x: cfg_data[x] for x in needed_keys
            }
        except KeyError:
            raise NoConfigFoundError(f"File at '{self._config_path}' is missing keys")

        with open(self._config_path, "w") as file_p:
            json.dump(new_config, file_p)
        self._reload()
