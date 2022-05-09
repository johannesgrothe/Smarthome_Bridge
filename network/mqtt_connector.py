import paho.mqtt.client as mqtt

from network.network_client import NetworkClient
from network.mqtt_server_client import MQTTServerClient
from network.mqtt_credentials_container import MqttCredentialsContainer


class MQTTConnector(NetworkClient):
    """Class to implement a MQTT connection module"""

    def __init__(self, hostname: str, credentials: MqttCredentialsContainer, channel: str):

        mqtt_client = mqtt.Client(hostname)

        if credentials.has_auth():
            mqtt_client.username_pw_set(credentials.username, credentials.password)

        try:
            mqtt_client.connect(credentials.ip, credentials.port)
        except OSError:
            pass

        mqtt_client.loop_start()
        mqtt_client.subscribe(f"{channel}/#")

        buf_server_client = MQTTServerClient(hostname, f"{credentials.ip}, {credentials.port}", mqtt_client, channel)

        super().__init__(hostname, buf_server_client)

    def __del__(self):
        super().__del__()
