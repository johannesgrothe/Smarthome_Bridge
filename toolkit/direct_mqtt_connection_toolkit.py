from toolkit.client_controller import ClientController
from network.mqtt_credentials_container import MqttCredentialsContainer
from toolkit.direct_connection_toolkit import DirectConnectionToolkit
from network.mqtt_connector import MQTTConnector
from typing import Optional


class DirectMqttConnectionToolkit(DirectConnectionToolkit):
    _mqtt_ip: str
    _mqtt_port: int
    _mqtt_username: Optional[str]
    _mqtt_password: Optional[str]

    def __init__(self, ip: str, port: int, username: Optional[str], password: Optional[str]):
        super().__init__()
        self._mqtt_ip = ip
        self._mqtt_port = port
        self._mqtt_username = username
        self._mqtt_password = password

        self._network.add_connector(MQTTConnector("ConsoleToolkit",
                                                  MqttCredentialsContainer(self._mqtt_ip,
                                                                           self._mqtt_port,
                                                                           self._mqtt_username,
                                                                           self._mqtt_password),
                                                  "smarthome"
                                                  ))
        pass

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        print("Please make sure your Client is connected to the network")

    def _scan_for_clients(self) -> [str]:
        return ClientController.detect_clients(self._network)
