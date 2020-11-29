import json
import paho.mqtt.client as mqtt
from typing import Optional
from bridge import MainBridge
from request import Request
from gadgetlib import GadgetIdentifier
from gadget import Characteristic, Gadget, CharacteristicIdentifier
from queue import Queue
from threading import Thread

# Global queue for mqtt results
mqtt_res_queue = Queue()


def gadget_type_to_string(identifier: GadgetIdentifier) -> Optional[str]:
    switcher = {
        1: "Lightbulb",
        2: "Fan",
        3: "Doorbell"
    }
    return switcher.get(identifier, None)

def characteristic_type_to_string(identifier: CharacteristicIdentifier) -> Optional[str]:
    switcher = {
        1: "On",
        2: "rotationSpeed",
        3: "brightness",
        4: "hue",
        5: "saturation"
    }
    return switcher.get(identifier, None)


class HomeKitRequest:
    topic: str
    message: dict

    def __init__(self, topic: str, message: dict):
        self.topic = topic
        self.message = message


class HomeConnector:

    __bridge: MainBridge

    def __init__(self, bridge: MainBridge):
        self.__bridge = bridge

    def register_gadget(self, gadget: Gadget):
        pass

    def update_characteristic(self, name: str, g_type: GadgetIdentifier,
                              characteristic: CharacteristicIdentifier, value: int):
        pass


class HomeKitConnector(HomeConnector):

    __own_name: str
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    __mqtt_callback_thread: Thread

    def __init__(self, bridge: MainBridge, own_name: str, mqtt_ip: str, mqtt_port: int, mqtt_user: Optional[str], mqtt_pw: Optional[str]):
        super().__init__(bridge)
        self.__own_name = own_name
        self.__client = mqtt.Client(self.__own_name + "_HomeBridge")
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)
        self.__client.connect(self.__ip, self.__port, 60)
        self.__client.loop_start()
        self.__client.on_message = self.__on_message
        self.__client.subscribe("homebridge/#")

        self.__mqtt_callback_thread = HomeKitMQTTThread(parent=self)
        self.__mqtt_callback_thread.start()

    def __del__(self):
        self.__client.disconnect()

    @staticmethod
    def __on_message(client, userdata, message):
        global mqtt_res_queue

        topic = message.topic
        json_str = message.payload.decode("utf-8")

        try:
            body = json.loads(json_str)
        except json.decoder.JSONDecodeError:
            print("Couldn't decode json: '{}'".format(json_str))
            return

        buf_req = HomeKitRequest(topic, body)

        mqtt_res_queue.put(buf_req)

    def register_gadget(self, gadget: Gadget):
        gadget_service = gadget_type_to_string(gadget.get_type())
        reg_str = {"name": gadget.get_name(), "service_name": gadget_service, "service": gadget_service}
        topic = "homebridge/to/add"
        buf_req = HomeKitRequest(topic, reg_str)
        self.__send_request(buf_req)

    def __send_request(self, req: HomeKitRequest):
        self.__client.publish(req.topic, json.dumps(req.message))

    def update_characteristic(self, name: str, g_type: GadgetIdentifier,
                              characteristic: CharacteristicIdentifier, value: int):
        gadget_service = gadget_type_to_string(g_type)
        reg_str = {"name": name,
                   "service_name": gadget_service,
                   "service": gadget_service,
                   "characteristic": characteristic_type_to_string(characteristic),
                  "value": value}
        topic = "homebridge/to/set"
        buf_req = HomeKitRequest(topic, reg_str)
        self.__send_request(buf_req)

    def handle_request(self, req: HomeKitRequest):
        pass


class HomeKitMQTTThread(Thread):
    __parent_object: HomeKitConnector

    def __init__(self, parent: HomeKitConnector):
        super().__init__()
        print("Starting HomeKitConnector MQTT Thread")
        self.__parent_object = parent
        self.__mqtt_connector = queue

    def run(self):
        global mqtt_res_queue
        while True:
            buf_req: Optional[HomeKitRequest] = mqtt_res_queue.get()
            if buf_req:
                self.__parent_object.handle_request(buf_req)


if __name__ == '__main__':
    import sys

    print(gadget_type_to_string(GadgetIdentifier(1)))

    # ip = "192.168.178.111"
    # port = 1883
    # try:
    #     test_hb_connector = HomeKitConnector("test", "192.168.178.111", 1883, None, None)
    # except OSError as e:
    #     print("Cannot connect to '{}:{}'".format(ip, port))
    #     sys.exit(1)
    #
    # test_hb_connector.register_gadget(Gadget("testgadget", GadgetIdentifier(1)))
