from network_connector import NetworkConnector, Request
from typing import Optional
import paho.mqtt.client as mqtt


class MQTTConnector(NetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: mqtt.Client
    __own_name: str
    __ip: str
    __port: int

    def __init__(self, own_name: str, ip: str, port: int):
        self.__own_name = own_name
        self.__client = mqtt.Client(self.__own_name)
        self.__ip = ip
        self.__port = port

        self.__client.connect(self.__ip, self.__port, 60)

    def __del__(self):
        self.__client.disconnect()

    def send_request(self, req: Request) -> (Optional[bool], Optional[Request]):
        self.__client.publish(req.get_path(), str(req.get_body()))


if __name__ == '__main__':
    mqtt_gadget = MQTTConnector("TesTeR", "192.168.178.111", 1883)

    buf_req = Request("smarthome/debug",
                      125543,
                      "me",
                      "you",
                      {"yolo": "blub"})

    mqtt_gadget.send_request(buf_req)
