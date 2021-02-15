import enum
import json
import time
import paho.mqtt.client as mqtt
from typing import Optional
from gadgetlib import GadgetIdentifier
from gadget import Characteristic, Gadget, CharacteristicIdentifier
from queue import Queue
from threading import Thread, Lock

# Global queue for mqtt results
mqtt_res_queue = Queue()


class HomeConnectorType(enum.IntEnum):
    """A number identifier for every gadget type"""
    err_type = 0
    homekit = 1


def gadget_type_to_string(identifier: GadgetIdentifier) -> Optional[str]:
    switcher = {
        1: "Lightbulb",
        2: "Fan",
        3: "Doorbell"
    }
    return switcher.get(identifier, None)


def characteristic_type_to_string(identifier: CharacteristicIdentifier) -> Optional[str]:
    """Takes a characteristic identifier and returns the fitting string. Returns None if nothing matches."""
    switcher = {
        1: "On",
        2: "rotationSpeed",
        3: "Brightness",
        4: "Hue",
        5: "Saturation"
    }
    return switcher.get(identifier, None)


def characteristic_str_to_type(characteristic: str) -> CharacteristicIdentifier:
    """Takes a string and returns the fitting characteristic identifier. Returns None if nothing matches."""
    switcher = {
        "On": CharacteristicIdentifier(1),
        "rotationSpeed": CharacteristicIdentifier(2),
        "Brightness": CharacteristicIdentifier(3),
        "Hue": CharacteristicIdentifier(4),
        "Saturation": CharacteristicIdentifier(5)
    }
    return switcher.get(characteristic, None)


class HomeKitRequest:
    topic: str
    message: dict

    def __init__(self, topic: str, message: dict):
        self.topic = topic
        self.message = message


class HomeConnector:

    __bridge = None

    __type: HomeConnectorType

    def __init__(self, bridge):
        self.__bridge = bridge
        self.__type = HomeConnectorType.err_type

    def register_gadget(self, gadget: Gadget):
        pass

    def update_characteristic(self, name: str, g_type: GadgetIdentifier,
                              characteristic: CharacteristicIdentifier, value: int):
        pass

    def __update_characteristic_on_bridge(self, name: str, characteristic: CharacteristicIdentifier, value: int):
        self.__bridge.update_characteristic_from_connector(name, characteristic, value)

    def serialized(self) -> dict:
        return {"type": int(self.__type)}


class HomeKitConnector(HomeConnector):

    __own_name: str
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    __mqtt_callback_thread: Thread

    # thread lock
    __lock: Lock
    __status_responses: Queue

    def __init__(self, bridge, own_name: str, mqtt_ip: str, mqtt_port: int,
                 mqtt_user: Optional[str] = None, mqtt_pw: Optional[str] = None):
        super().__init__(bridge)
        self.__own_name = own_name
        self.__client = mqtt.Client(self.__own_name + "_HomeBridge")
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)
        try:
            self.__client.connect(self.__ip, self.__port, 15)
        except OSError:
            print("Could not connect to MQTT Server.")
        self.__client.loop_start()
        self.__client.on_message = self.__on_message
        self.__client.subscribe("homebridge/#")

        self.__mqtt_callback_thread = HomeKitMQTTThread(parent=self)
        self.__mqtt_callback_thread.start()

        self.__type = HomeConnectorType.homekit

        self.__lock = Lock()

    def __del__(self):
        self.__client.disconnect()

    def get_name(self) -> str:
        return self.__own_name

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
        """Registers a gadget on the homebridge remote"""

        # {"name": "flex_lamp", "service_name": "flex_lamp", "service": "Lightbulb",
        #  "Brightness": {"minValue": 0, "maxValue": 100, "minStep": 1},
        #  "Hue": {"minValue": 0, "maxValue": 360, "minStep": 1},
        #  "Saturation": {"minValue": 0, "maxValue": 100, "minStep": 1}}

        gadget_service = gadget_type_to_string(gadget.get_type())
        reg_dict = {"name": gadget.get_name(), "service_name": gadget_service, "service": gadget_service}
        topic = "homebridge/to/add"

        for characteristic in gadget.get_characteristic_types():
            characteristic_str = characteristic_type_to_string(characteristic)
            if characteristic_str:
                min_v, max_v, step_v = gadget.get_characteristic_options(characteristic)
                if min_v is not None:
                    reg_dict[characteristic_str] = {"minValue": min_v, "minVal": max_v, "maxStep": step_v}
        buf_req = HomeKitRequest(topic, reg_dict)
        self.__send_request(buf_req)

    def remove_gadget(self, gadget: Gadget):
        """Removes a gadget from the homebridge remote"""
        buf_req = HomeKitRequest("homebridge/to/remove", {"name": gadget.get_name()})
        self.__send_request(buf_req)

    def __send_request(self, req: HomeKitRequest):
        self.__client.publish(req.topic, json.dumps(req.message))

    def update_characteristic(self, name: str, g_type: GadgetIdentifier,
                              characteristic: CharacteristicIdentifier, value: int) -> bool:
        gadget_service = gadget_type_to_string(g_type)
        reg_str = {"name": name,
                   "service_name": gadget_service,
                   "service": gadget_service,
                   "characteristic": characteristic_type_to_string(characteristic),
                   "value": value}

        topic = "homebridge/to/set"
        buf_req = HomeKitRequest(topic, reg_str)
        with self.__lock:
            self.__send_request(buf_req)
            start_time = time.time()
            while time.time() < start_time + 5:
                if not self.__status_responses.empty():
                    resp: HomeKitRequest = self.__status_responses.get()
                    if resp.message["ack"]:
                        print("Updating Characteristic was successful")
                        return True
                    else:
                        print("failed to update characteristic")
                        return False
        return False

    def handle_request(self, req: HomeKitRequest):
        # Just store request in the response queue for waiting processes to access
        if req.topic == "homebridge/from/response" and "ack" in req.message:
            self.__status_responses.put(req)
            return

        # Check handle characteristic updates
        if req.topic == "homebridge/from/set":
            # {"name": "flex_lamp", "service_name": "flex_lamp", "service_type": "Lightbulb",
            #  "characteristic": "Brightness", "value": 47}
            if not ("name" in req.message and "characteristic" in req.message and "value" in req.message):
                print("Received broken characteristic update request")
                return
            self.__update_characteristic_on_bridge(req.message["name"],
                                                   req.message["characteristic"],
                                                   req.message["value"])


class HomeKitMQTTThread(Thread):
    __parent_object: HomeKitConnector

    def __init__(self, parent: HomeKitConnector):
        super().__init__()
        print("Starting HomeKitConnector MQTT Thread")
        self.__parent_object = parent
        self.__mqtt_connector = Queue

    def run(self):
        global mqtt_res_queue
        while True:
            buf_req: Optional[HomeKitRequest] = mqtt_res_queue.get()
            if buf_req:
                self.__parent_object.handle_request(buf_req)


if __name__ == '__main__':

    print(gadget_type_to_string(GadgetIdentifier(1)))

    # ip = "192.168.178.111"
    # port = 1883
    # try:
    #     test_hb_connector = HomeKitConnector("test", "192.168.178.111", 1883, None, None)
    # except OSError as e:
    #     print("Cannot connect to '{}:{}'".format(ip, port))
    #     sys.exit(1)
    #
    # test_hb_connector.register_gadget(Gadget("test_gadget", GadgetIdentifier(1)))
