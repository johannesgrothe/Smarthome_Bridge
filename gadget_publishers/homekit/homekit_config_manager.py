import json
import random
import socket

from lib.logging_interface import LoggingInterface


class HomekitConfigManager(LoggingInterface):
    _config_path: str

    def __init__(self, config_path: str):
        super().__init__()
        self._config_path = config_path

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
    def _generate_pairing_id() -> str:
        id_bytes = [hex(random.randint(0, 255)) for _ in range(7)]
        return ":".join(id_bytes)

    def generate_new_config(self) -> None:
        """
        Generates an all new config and replaces any old one (including all pairing information)

        :return: None
        """
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

    def reset_config_pairings(self) -> None:
        """
        Removes all pairing information from config

        :return: None
        """
        with open(self._config_path, "r") as file_p:
            cfg_data = json.load(file_p)

        new_config = {
            x: cfg_data[x] for x in ["accessory_pairing_id", "accessory_pin",
                                     "c#", "category", "host_ip", "host_port",
                                     "name"]
        }

        with open(self._config_path, "w") as file_p:
            json.dump(new_config, file_p)
