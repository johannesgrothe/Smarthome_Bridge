import api
import argparse
import json
import socket
import random
import sys
import webinterface
from gadget import Gadget
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

    __bridge_name: str

    __mqtt_port: int
    __mqtt_ip: str
    __mqtt_user: Optional[str]
    __mqtt_pw: Optional[str]

    __gadgets: [Gadget]
    __network_gadget: MQTTConnector

    def __init__(self, bridge_name: str, mqtt_port: int, mqtt_ip: str, mqtt_username: Optional[str], mqtt_pw: Optional[str]):
        self.__bridge_name = bridge_name

        self.__mqtt_ip = mqtt_ip
        self.__mqtt_port = mqtt_port
        self.__mqtt_user = mqtt_username
        self.__mqtt_pw = mqtt_pw

        self.__gadgets = []
        self.__network_gadget = MQTTConnector(self.__bridge_name,
                                              self.__mqtt_ip,
                                              self.__mqtt_port)

    def get_bridge_name(self) -> str:
        return self.__bridge_name

    def update_characteristic(self, gadget_name: str, characteristic_name: str, value: int) -> bool:
        for buf_gadget in self.__gadgets:
            if buf_gadget.get_name() == gadget_name:
                return buf_gadget.update_characteristic(characteristic_name, value)
        return False






if __name__ == '__main__':

    if ARGS.mqtt_port:
        mqtt_port = int(ARGS.mqtt_port)
    else:
        print("No Port selected.")
        sys.exit(21)

    if ARGS.mqtt_ip:
        mqtt_ip = ARGS.mqtt_ip
    else:
        print("No IP selected.")
        sys.exit(22)

    bridge = MainBridge(get_sender(), mqtt_ip, mqtt_port)

    gadget: [Gadget] = []

    api.run_api("TestInstance")