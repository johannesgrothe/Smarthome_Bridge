from network.network_client import NetworkClient
from network.mqtt_server_client import MQTTServerClient
from typing import Optional
import paho.mqtt.client as mqtt
import json

from network.request import Request


class MQTTConnector(NetworkClient):
    """Class to implement a MQTT connection module"""

    __client: mqtt.Client
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    def __init__(self, hostname: str, mqtt_ip: str, mqtt_port: int, mqtt_user: Optional[str] = None,
                 mqtt_pw: Optional[str] = None):

        self.__client = mqtt.Client(hostname)
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)

        try:
            self.__client.connect(self.__ip, self.__port, 10)
        except OSError:
            self._logger.error("Could not connect to MQTT Server.")

        self.__client.loop_start()
        self.__client.subscribe("smarthome/#")

        buf_client = MQTTServerClient(hostname, f"{self.__ip}, {self.__port}", self.__client)

        super().__init__(hostname, buf_client)

    def __del__(self):
        super().__del__()

    def _send_data(self, req: Request):
        self.__client.publish(req.get_path(), json.dumps(req.get_body()))
