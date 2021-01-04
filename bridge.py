import argparse
import socket
import random
import sys
import os
import time
from threading import Thread
import threading
from datetime import datetime
from chip_flasher import flash_chip, get_serial_ports

from homekit_connector import HomeConnectorType, HomeKitConnector
from smarthomeclient import SmarthomeClient
from gadget import Gadget, GadgetIdentifier, CharacteristicIdentifier, CharacteristicUpdateStatus, Characteristic
from typing import Optional
from mqtt_connector import MQTTConnector
from request import Request
import api
import websocket_api
import client_control_methods


def gen_req_id() -> int:
    """Generates a random Request ID"""
    return random.randint(0, 1000000)


def get_sender() -> str:
    """Returns the name used as sender (local hostname)"""
    return socket.gethostname()


def check_dict_for_keys(check_dict: dict, key_list: [str]) -> bool:
    """Checks if all given keys are included in the dict"""
    for key in key_list:
        if key not in check_dict:
            return False
    return True


def fill_with_nones(check_dict: dict, key_list: [str]) -> dict:
    """Checks if every of the given keys are present and adds the missing keys with a None value"""
    buf_dict = check_dict
    for key in key_list:
        if key not in buf_dict:
            buf_dict[key] = None
    return buf_dict


class MainBridge:
    """Main Bridge for the Smarthome Environment"""

    # Name of the bridge
    __bridge_name: str

    # Bridge software commit hash
    __sw_commit: Optional[str]

    # Bridge software commit branch
    __sw_branch: Optional[str]

    # Time the bridge was launched
    __time_launched: datetime

    # MQTT
    __mqtt_port: int
    __mqtt_ip: str
    __mqtt_user: Optional[str]
    __mqtt_pw: Optional[str]

    # API
    __api_port: int
    __api_thread: Thread
    __ws_api_port: int

    __network_gadget: MQTTConnector
    __mqtt_callback_thread: Thread
    __received_requests: int

    # Gadgets:
    __gadgets: [Gadget]

    # Clients
    __clients: [SmarthomeClient]

    # Connectors
    __connectors = []

    # thread lock
    __lock = None

    def __init__(self, bridge_name: str, mqtt_ip: str, mqtt_port: int,
                 mqtt_username: Optional[str], mqtt_pw: Optional[str]):
        print("Setting up Bridge...")

        # Setting bridge name
        self.__bridge_name = bridge_name

        # Setting counter for received requests to 0
        self.__received_requests = 0

        # Setting the value for the software commit hash
        self.__sw_commit = os.popen("git rev-parse HEAD").read().strip("\n")
        if self.__sw_commit == "":
            self.__sw_commit = None

        # Setting the value for the software branch
        self.__sw_branch = os.popen("git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)")\
            .read().strip("\n")
        if self.__sw_branch == "":
            self.__sw_branch = None

        # Set launch time
        self.__time_launched = datetime.now()

        # MQTT
        self.__mqtt_ip = mqtt_ip
        self.__mqtt_port = mqtt_port
        self.__mqtt_user = mqtt_username
        self.__mqtt_pw = mqtt_pw

        # API
        self.__api_port = 0
        self.__ws_api_port = 0

        self.__clients = []
        self.__gadgets = []
        self.__connectors = []

        print("Setting up Network...")
        self.__network_gadget = MQTTConnector(self.__bridge_name,
                                              self.__mqtt_ip,
                                              self.__mqtt_port,
                                              None,
                                              None)
        self.__mqtt_callback_thread = BridgeMQTTThread(parent=self,
                                                       connector=self.__network_gadget)
        self.__mqtt_callback_thread.start()

        self.__lock = threading.Lock()
        print("Ok.")

    def add_dummy_data(self):
        self.__add_client("dummy_client1",
                          1234567)
        self.add_gadget(Gadget("dummy_lamp",
                               GadgetIdentifier(1),
                               "dummy_client1",
                               1234567,
                               [
                                   Characteristic(CharacteristicIdentifier(1),
                                                  0,
                                                  1,
                                                  1,
                                                  1),
                                   Characteristic(CharacteristicIdentifier(3),
                                                  0,
                                                  100,
                                                  1,
                                                  35)
                               ]))
        self.add_gadget(Gadget("dummy_fan",
                               GadgetIdentifier(3),
                               "dummy_client1",
                               1234567,
                               [
                                   Characteristic(CharacteristicIdentifier(1),
                                                  0,
                                                  100,
                                                  1,
                                                  35),
                                   Characteristic(CharacteristicIdentifier(2),
                                                  0,
                                                  100,
                                                  33,
                                                  66)
                               ]))
        self.__add_connector(HomeConnectorType(1), {"name": "test_connector1",
                                                    "ip": "192.168.178.111",
                                                    "port": 1883})

    def handle_request(self, req: Request):
        """Receives a request from the watcher Thread and handles it"""
        self.__received_requests += 1

        if req.get_receiver() != "<bridge>":
            return

        print("Received Request Nr. {}: {}".format(self.__received_requests + 1, req.get_path()))

        req_pl: dict = req.get_payload()

        # Check if the request was sent by any known client and report activity
        if req.get_path() == "smarthome/heartbeat":
            local_client = self.__get_or_create_client_from_request(req)
            if local_client.needs_update():
                self.__ask_for_update(local_client)

        # TODO: add time sync

        # Check if the request was sent by any known client and report activity
        if req.get_path() == "smarthome/sync":

            local_client = self.__get_or_create_client_from_request(req)

            all_keys_existing = check_dict_for_keys(req_pl, ["runtime_id", "gadgets", "port_mapping", "boot_mode"])
            if not all_keys_existing:
                print("Request is missing keys")

            req_pl = fill_with_nones(req_pl, ["sw_uploaded", "sw_commit", "sw_branch"])

            if not isinstance(req_pl["gadgets"], list):
                print("Gadget config in sync response was no list")
                return

            print("Received sync data from '{}'".format(local_client.get_name()))

            updated_gadgets: [str] = []

            # Go over all gadgets and create or update them
            for list_gadget in req_pl["gadgets"]:

                # If a gadget fails, it fails. That's why theres a giant try block.
                try:
                    g_name = list_gadget["name"]
                    g_type = GadgetIdentifier(list_gadget["type"])
                    g_characteristics = []
                    for characteristic in list_gadget["characteristics"]:
                        # Create new characteristic
                        new_c = Characteristic(CharacteristicIdentifier(characteristic["type"]),
                                               characteristic["min"],
                                               characteristic["max"],
                                               characteristic["step"],
                                               characteristic["value"])
                        # Save it
                        g_characteristics.append(new_c)

                    # Get the gadget if there is already one in existence with the correct name
                    buf_gadget: Optional[Gadget] = self.get_gadget(g_name)
                    if buf_gadget is not None:
                        # Update existing gadget
                        print("Updating '{}'".format(buf_gadget.get_name()))
                        buf_gadget.update_gadget_info(g_type,
                                                      req.get_sender(),
                                                      req_pl["runtime_id"],
                                                      g_characteristics)
                    else:
                        # Create new gadget since there is no gadget with selected name
                        print("Creating new '{}'".format(g_name))
                        buf_gadget = Gadget(g_name,
                                            g_type,
                                            req.get_sender(),
                                            req_pl["runtime_id"],
                                            g_characteristics)
                        self.add_gadget(buf_gadget)

                    # Save name of gadget to skip deletion
                    updated_gadgets.append(buf_gadget.get_name())

                except KeyError as e:
                    print("Error syncing gadget:")
                    print(e)

            deleted_gadgets = 0

            for gadget in self.__gadgets:
                if gadget.get_host_client() == req.get_sender():
                    if gadget.get_name() not in updated_gadgets:
                        self.delete_gadget(gadget)
                        deleted_gadgets += 1

            print("Updated {} Gadgets".format(len(updated_gadgets)))
            print("Deleted {} Gadgets".format(deleted_gadgets))

            # Report update to client
            local_client.update_data(req_pl["sw_uploaded"], req_pl["sw_commit"],
                                     req_pl["sw_branch"], req_pl["port_mapping"],
                                     req_pl["boot_mode"])

            print("Update finished.")

            return

        # Receive gadget characteristic update from client
        if req.get_path() == "smarthome/remotes/gadget/update":
            if "name" not in req_pl:
                print("No name in characteristic update message")
                return

            if "characteristic" not in req_pl:
                print("No characteristic in characteristic update message")
                return

            if "value" not in req_pl:
                print("No value in characteristic update message")
                return

            print("Received update for characteristic '{}' from '{}'".format(req_pl["name"],
                                                                             req_pl["characteristic"]))

            self.update_characteristic_from_client(req_pl["name"],
                                                   CharacteristicIdentifier(req_pl["characteristic"]),
                                                   req_pl["value"])
            return

    @staticmethod
    def flash_software(branch: str = "master", serial_port: str = "/dev/cu.SLAB_USBtoUART") -> bool:
        """Flashes the Smarthome_ESP32 software from the selected branch to the chip"""
        return flash_chip(branch, False, serial_port)

    @staticmethod
    def get_serial_ports() -> [str]:
        """Returns all serial ports existing on the system"""
        return get_serial_ports()

    # region BRIDGE DATA

    def get_bridge_name(self) -> str:
        """Sets the name for the bridge"""
        with self.__lock:
            return self.__bridge_name

    def get_time_launched(self) -> datetime:
        """Returns the time the bridge got started"""
        with self.__lock:
            return self.__time_launched

    def get_sw_commit(self) -> Optional[str]:
        """Returns the software commit hash of the bridge"""
        with self.__lock:
            return self.__sw_commit

    def get_sw_branch(self) -> Optional[str]:
        """Returns the software branch of the bridge"""
        with self.__lock:
            return self.__sw_branch

    # endregion

    # region CLIENT METHODS
    def get_client(self, name: str) -> Optional[SmarthomeClient]:
        with self.__lock:
            for client in self.__clients:
                if client.get_name() == name:
                    return client
        return None

    def __add_client(self, name: str, runtime_id: int) -> bool:
        if self.get_client(name) is None:
            with self.__lock:
                buf_client = SmarthomeClient(name, runtime_id)
                self.__clients.append(buf_client)
                return True
        return False

    def get_all_clients(self) -> [SmarthomeClient]:
        """Returns a list of all saved clients"""
        with self.__lock:
            return self.__clients
        pass

    @staticmethod
    def __trigger_client(client: SmarthomeClient):
        """Reports an activity signal from a client"""
        print("Triggering Activity on Client: '{}'".format(client.get_name()))
        client.trigger_activity()

    def __get_or_create_client(self, name: str, runtime_id: int) -> Optional[SmarthomeClient]:
        """Searches for a client with the name, creates it if necessary and returns the client"""
        local_client = self.get_client(name)
        if local_client is None:
            success = self.__add_client(name, runtime_id)
            local_client = self.get_client(name)
            if local_client is None or not success:
                return None
        return local_client

    def __get_or_create_client_from_request(self, req: Request) -> Optional[SmarthomeClient]:
        """Searches for a client with the name, creates it if necessary and returns the client"""
        if "runtime_id" not in req.get_payload():
            print("Received heartbeat is missing 'runtime_id'")
            return None

        if not isinstance(req.get_payload()["runtime_id"], int):
            print("Received heartbeat has non-integer 'runtime_id'")
            return None

        local_client = self.__get_or_create_client(req.get_sender(), req.get_payload()["runtime_id"])
        if local_client is None:
            print("Something went completely wrong while creating client")
            return None

        self.__trigger_client(local_client)
        local_client.update_runtime_id(req.get_payload()["runtime_id"])

        return local_client

    def __ask_for_update(self, client: SmarthomeClient):
        """Sends out a request asking the selected client to send an update"""
        out_req = Request("smarthome/sync",
                          gen_req_id(),
                          "<bridge>",
                          client.get_name(),
                          {"server_time": int(time.time() / 1000)})
        self.__network_gadget.send_request(out_req, timeout=0)

    def restart_client(self, client: SmarthomeClient) -> bool:
        """Sends out a request to restart the client and"""

        return client_control_methods.reboot_client(client.get_name(),
                                                    "<bridge>",
                                                    self.__network_gadget)

    # endregion

    # region CHARACTERISTIC METHODS
    def update_characteristic_on_gadget(self, gadget_name: str, characteristic: CharacteristicIdentifier,
                                        value: int) -> (CharacteristicUpdateStatus, Gadget):
        """Updates a single characteristic of the selected gadget"""
        with self.__lock:
            for buf_gadget in self.__gadgets:
                if buf_gadget.get_name() == gadget_name:
                    return buf_gadget.update_characteristic(characteristic, value), buf_gadget
        return CharacteristicUpdateStatus.general_error, None

    def update_characteristic_from_client(self, gadget_name: str, characteristic: CharacteristicIdentifier,
                                          value: int) -> CharacteristicUpdateStatus:
        """Updates a single characteristic of the selected gadget"""
        update_status, gadget = self.update_characteristic_on_gadget(gadget_name, characteristic, value)
        if update_status == CharacteristicUpdateStatus.update_successful:
            self.update_characteristic_on_connectors(gadget, characteristic, value)
        return update_status

    def update_characteristic_on_clients(self, gadget: Gadget, characteristic: CharacteristicIdentifier,
                                         value: int) -> bool:
        """Forwards a characteristic update to the clients"""

        req_id = gen_req_id()

        buf_request = Request("smarthome/remotes/gadget/to_client/update",
                              req_id,
                              "<bridge>",
                              gadget.get_host_client(),
                              {
                                  "name": gadget.get_name(),
                                  "characteristic": int(characteristic),
                                  "value": value
                              })

        # Sends the request and does not wait for any answer
        self.__network_gadget.send_request(buf_request, 0)
        return False

    def update_characteristic_from_connector(self, gadget_name: str, characteristic: CharacteristicIdentifier,
                                             value: int, sender) -> CharacteristicUpdateStatus:
        """Gets an characteristic update from a connector and forwards it to every other connector and the clients"""
        update_status, gadget = self.update_characteristic_on_gadget(gadget_name, characteristic, value)
        if update_status == CharacteristicUpdateStatus.update_successful:
            # Update characteristic on clients
            self.update_characteristic_on_clients(gadget, characteristic, value)

            # Update characteristic on every other sender
            self.update_characteristic_on_connectors(gadget, characteristic, value, sender)

        return update_status

    def update_characteristic_on_connectors(self, gadget: Gadget, characteristic: CharacteristicIdentifier,
                                            value: int, exclude=None) -> bool:
        for connector in self.__connectors:
            if exclude is not None and connector != exclude:
                connector.update_characteristic(gadget.get_name(), characteristic, value)
        return True

    # endregion

    # region GADGET METHODS
    def get_gadget(self, gadget_name: str) -> Optional[Gadget]:
        """Returns the data for the selected gadget"""
        with self.__lock:
            for buf_gadget in self.__gadgets:
                if buf_gadget.get_name() == gadget_name:
                    return buf_gadget
            return None

    def get_all_gadgets(self):
        """Returns the data for all gadgets"""
        with self.__lock:
            return self.__gadgets

    def add_gadget(self, gadget: Gadget) -> bool:
        """Adds a gadget to the bridge"""
        if self.get_gadget(gadget.get_name()):
            print("Gadget with this name is already present")
            return False
        with self.__lock:
            print("Adding new gadget '{}'".format(gadget.get_name()))
            self.__gadgets.append(gadget)
            return True

    def delete_gadget(self, gadget: Gadget):
        """Deletes the passed gadget from all connectors and the local storage"""
        with self.__lock:
            for connector in self.__connectors:
                connector.remove_gadget(gadget)

            self.__gadgets.remove(gadget)

    # endregion

    # region CONNECTOR METHODS
    def get_all_connectors(self):
        """Returns the data for all connectors"""
        with self.__lock:
            return self.__connectors

    def __add_connector(self, c_type: HomeConnectorType, data: dict):
        if c_type == HomeConnectorType.homekit:
            try:
                buf_connector = HomeKitConnector(self,
                                                 own_name=data["name"],
                                                 mqtt_ip=data["ip"],
                                                 mqtt_port=data["port"])
                self.__connectors.append(buf_connector)
                print("Added 'HomeKit' connector '{}'".format(buf_connector.get_name()))
            except KeyError:
                print("Received broken connector config")

            return

    # endregion

    # region API
    def set_api_port(self, port: int):
        """Sets the port for the REST API"""
        with self.__lock:
            self.__api_port = port

    def get_api_port(self):
        """returns the current API port of the bridge"""
        with self.__lock:
            return self.__api_port

    def run_api(self):
        """Launches the REST API"""
        with self.__lock:
            self.__api_thread = BridgeAPIThread(parent=self)
            self.__api_thread.start()

    def set_ws_api_port(self, port: int):
        """Sets the port for the REST API"""
        with self.__lock:
            self.__ws_api_port = port

    def get_ws_api_port(self):
        """returns the current API port of the bridge"""
        with self.__lock:
            return self.__ws_api_port

    def run_ws_api(self):
        """Launches the REST API"""
        with self.__lock:
            self.__api_thread = BridgeWSAPIThread(parent=self)
            self.__api_thread.start()

    # endregion

    def get_streaming_message(self) -> Optional[str]:
        with self.__lock:
            return "blub"


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


class BridgeAPIThread(Thread):
    __parent_object: MainBridge

    def __init__(self, parent: MainBridge):
        super().__init__()
        print("Starting Bridge API Thread")
        self.__parent_object = parent

    def run(self):
        buf_api_port = self.__parent_object.get_api_port()

        if buf_api_port == 0:
            print("API port not configured")
            return

        print("Launching API")
        api.run_api(self.__parent_object, buf_api_port)


class BridgeWSAPIThread(Thread):
    __parent_object: MainBridge

    def __init__(self, parent: MainBridge):
        super().__init__()
        print("Starting Bridge Websocket API Thread")
        self.__parent_object = parent

    def run(self):
        buf_api_port = self.__parent_object.get_ws_api_port()

        if buf_api_port == 0:
            print("Websocket API port not configured")
            return

        print("Launching Websocket API")
        websocket_api.run_websocket_api(self.__parent_object, buf_api_port)


if __name__ == '__main__':
    # Argument-parser
    parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
    parser.add_argument('--mqtt_ip', help='mqtt ip to be uploaded.', type=str)
    parser.add_argument('--mqtt_port', help='port to be uploaded.', type=int)
    parser.add_argument('--mqtt_user', help='mqtt username to be uploaded.', type=str)
    parser.add_argument('--mqtt_pw', help='mqtt password to be uploaded.', type=str)
    parser.add_argument('--dummy_data', help='Adds dummy data for debugging.', action="store_true")
    ARGS = parser.parse_args()

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

    # Create Bridge
    bridge = MainBridge(get_sender(), buf_mqtt_ip, buf_mqtt_port, None, None)

    # Insert dummy data if wanted
    if ARGS.dummy_data:
        print("Adding dummy data:")
        bridge.add_dummy_data()

    # Set API Ports
    bridge.set_api_port(4999)
    bridge.set_ws_api_port(6200)

    # Start API Threads
    # bridge.run_api()
    bridge.run_ws_api()
