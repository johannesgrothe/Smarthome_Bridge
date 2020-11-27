import api
import argparse
import json
import socket
import random
import sys
from threading import Thread
from gadget import Gadget, GadgetIdentifier, CharacteristicIdentifier
from typing import Optional
from mqtt_connector import MQTTConnector
from request import Request

parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
parser.add_argument('--mqtt_ip', help='mqtt ip to be uploaded.')
parser.add_argument('--mqtt_port', help='port to be uploaded.')
parser.add_argument('--mqtt_user', help='mqtt username to be uploaded.')
parser.add_argument('--mqtt_pw', help='mqtt password to be uploaded.')
ARGS = parser.parse_args()


def gen_req_id() -> int:
    """Generates a random Request ID"""
    return random.randint(0, 1000000)


def get_sender() -> str:
    """Returns the name used as sender (local hostname)"""
    return socket.gethostname()


class MainBridge:
    """Main Bridge for the Smarthome Environment"""

    __bridge_name: str

    # MQTT
    __mqtt_port: int
    __mqtt_ip: str
    __mqtt_user: Optional[str]
    __mqtt_pw: Optional[str]

    # API
    __api_port: int

    __network_gadget: MQTTConnector
    __mqtt_callback_thread: Thread
    __received_requests: int

    # Gadgets:
    __gadgets: [Gadget]

    def __init__(self, bridge_name: str, mqtt_ip: str, mqtt_port: int,
                 mqtt_username: Optional[str], mqtt_pw: Optional[str]):
        print("Setting up Bridge...")
        self.__bridge_name = bridge_name
        self.__received_requests = 0

        # MQTT
        self.__mqtt_ip = mqtt_ip
        self.__mqtt_port = mqtt_port
        self.__mqtt_user = mqtt_username
        self.__mqtt_pw = mqtt_pw

        # API
        self.__api_port = 5000

        self.__gadgets = []
        print("Setting up Network...")
        self.__network_gadget = MQTTConnector(self.__bridge_name,
                                              self.__mqtt_ip,
                                              self.__mqtt_port,
                                              None,
                                              None)
        self.__mqtt_callback_thread = BridgeMQTTThread(parent=self,
                                                       connector=self.__network_gadget)
        self.__mqtt_callback_thread.start()
        print("Ok.")

    def get_bridge_name(self) -> str:
        """Sets the name for the bridge"""
        return self.__bridge_name

    def handle_request(self, req: Request):
        """Receives a request from the watcher Thread and handles it"""
        print("Received Request Nr. {}: {}".format(self.__received_requests + 1, req.get_path()))
        self.__received_requests += 1

        if req.get_receiver() != "<bridge>":
            return

        req_pl: dict = req.get_payload()

        if req.get_path() == "smarthome/remotes/gadget/register":

            if not ("gadget_name" in req_pl and "gadget_type" in req_pl and "characteristics" in req_pl):
                print("Missing arguments in register payload")
                return

            try:
                gadget_ident = GadgetIdentifier(req_pl["gadget_type"])
            except ValueError:
                print("Received illegal gadget identifier")
                return

            buf_gadget = Gadget(name=req_pl["gadget_name"],
                                g_type=gadget_ident)

            for ch_name in req_pl["characteristics"]:
                buf_characteristic = req_pl["characteristics"][ch_name]

                try:
                    characteristic_type = CharacteristicIdentifier(int(ch_name))

                    buf_gadget.add_characteristic(c_type=characteristic_type,
                                                  min_val=buf_characteristic["min"],
                                                  max_val=buf_characteristic["max"],
                                                  step=buf_characteristic["step"])

                except ValueError:
                    print("received illegal characteristic identifier '{}'".format(ch_name))

            _ = self.add_gadget(buf_gadget)

    # Characteristics
    def update_characteristic(self, gadget_name: str, characteristic_name: str, value: int) -> bool:
        """Updates a single characteristic of the selected gadget"""
        for buf_gadget in self.__gadgets:
            if buf_gadget.get_name() == gadget_name:
                return buf_gadget.update_characteristic(characteristic_name, value)
        return False

    # Gadgets
    def get_gadget(self, gadget_name: str) -> Optional[Gadget]:
        """Returns the data for the selected gadget"""
        for buf_gadget in self.__gadgets:
            if buf_gadget.get_name() == gadget_name:
                return buf_gadget
        return None

    def get_all_gadgets(self):
        """Returns the data for all gadgets"""
        return self.__gadgets

    def add_gadget(self, gadget: Gadget) -> bool:
        if self.get_gadget(gadget.get_name()):
            print("Gadget with this name is already present")
            return False
        print("Adding new gadget '{}'".format(gadget.get_name()))
        self.__gadgets.append(gadget)
        return True

    # API settings
    def set_api_port(self, port: int):
        """Sets the port for the REST API"""
        self.__api_port = port

    def run_api(self):
        """Launches the REST API"""
        print("Launching API")
        api.run_api(bridge, self.__api_port)


class BridgeMQTTThread(Thread):
    __parent_object: MainBridge
    __mqtt_connector: MQTTConnector

    def __init__(self, parent: MainBridge, connector: MQTTConnector):
        super().__init__()
        print("Starting Bridge MQTT Thread")
        self.__parent_object = parent
        self.__mqtt_connector = connector

    def run(self):
        while True:
            buf_req: Optional[Request] = self.__mqtt_connector.get_request()
            if buf_req:
                self.__parent_object.handle_request(buf_req)


if __name__ == '__main__':
    print("Launching Bridge")

    if ARGS.mqtt_port:
        buf_mqtt_port = int(ARGS.mqtt_port)
    else:
        print("No Port selected.")
        sys.exit(21)

    if ARGS.mqtt_ip:
        buf_mqtt_ip = ARGS.mqtt_ip
    else:
        print("No IP selected.")
        sys.exit(22)

    bridge = MainBridge(get_sender(), buf_mqtt_ip, buf_mqtt_port, None, None)

    bridge.set_api_port(4999)
    bridge.run_api()

    bridge.set_webinterface_port(3999)
    bridge.run_webinterface()
