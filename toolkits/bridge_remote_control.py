import os
import socket
import argparse
import sys
import threading

import requests
import json
import gadgetlib
import logging
import random
import time
from abc import ABCMeta, abstractmethod
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier
from typing import Optional
from tools import git_tools
from serial_connector import SerialConnector
from mqtt_connector import MQTTConnector
from network_connector import NetworkConnector, Request
from request import NoClientResponseException
from chip_flasher import ChipFlasher
from client_controller import ClientController
from client_config_manager import ClientConfigManager
from toolkit_settings_manager import ToolkitSettingsManager, InvalidConfigException

TOOLKIT_NETWORK_NAME = "ConsoleToolkit"

DIRECT_NETWORK_MODES = ["serial", "mqtt"]
BRIDGE_FUNCTIONS = ["Write software to chip", "Write config to chip", "Reboot chip", "Update Toolkit"]
DEFAULT_SW_BRANCH_NAMES = ["Enter own branch name", "master", "develop"]
CONFIG_FLASH_OPTIONS = ["Direct", "Wifi"]


class LoadingIndicator:

    _running: bool
    _run_thread: Optional[threading.Thread]

    def __init__(self):
        self._running = False
        self._run_thread = None

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _thread_runner(self):
        while self._running:
            print(".", end="")
            time.sleep(0.25)

    def _stop_thread(self):
        self._running = False
        if self._run_thread:
            self._run_thread.join()

    def run(self):
        self._stop_thread()

        print("[", end="")
        self._running = True
        self._run_thread = threading.Thread(target=self._thread_runner)
        self._run_thread.start()

    def stop(self):
        if self._running:
            print("]")
            self._stop_thread()


def ask_for_continue(message: str) -> bool:
    """Asks the user if he wishes to continue."""
    while True:
        print(f"{message} [y/n]")
        res = input().strip().lower()
        if res == "y":
            return True
        elif res == "n":
            return False
        print("Illegal Input, please try again.")


def enter_file_path() -> Optional[str]:
    """Asks the User to enter a file path. Returns None if the input is no valid file path."""
    print("Please enter the path to the file or drag it into the terminal window:")
    f_path = input()
    if not f_path or not os.path.isfile(f_path):
        return None
    return f_path


def gen_req_id() -> int:
    """Generates a random Request ID"""

    return random.randint(0, 1000000)


def select_option(input_list: [str], category: Optional[str] = None, back_option: Optional[str] = None) -> int:
    """Presents every elem from the list and lets the user select one"""

    if category is None:
        print("Please select:")
    else:
        print("Please select {} {}:".format(
            'an' if category[0].lower() in ['a', 'e', 'i', 'o', 'u'] else 'a',
            category))
    max_i = 0
    for i in range(len(input_list)):
        print("    {}: {}".format(i, input_list[i]))
        max_i += 1
    if back_option:
        print("    {}: {}".format(max_i + 1, back_option))
        max_i += 1

    selection = None
    while selection is None:
        selection = input("Please select an option by entering its number:\n")
        try:
            selection = int(selection)
        except (TypeError, ValueError):
            selection = None

        if selection is None or selection < 0 or selection > max_i:
            print("Illegal input, try again.")
            selection = None
    if selection == max_i:
        selection = -1
    return selection


def read_serial_ports_from_bridge() -> [str]:
    res_status, serial_port_data = send_api_request(f"{bridge_addr}:{api_port}/system/get_serial_ports")
    if res_status == 200:
        if "serial_ports" in serial_port_data:
            return serial_port_data["serial_ports"]
    return []


def read_configs_from_bridge() -> [str]:
    res_status, config_list_data = send_api_request(f"{bridge_addr}:{api_port}/system/configs")
    if res_status == 200:
        if "config_names" in config_list_data:
            return config_list_data["config_names"]
    return []


def read_config_from_bridge(cfg_name: str) -> Optional[dict]:
    res_status, config_data = send_api_request(f"{bridge_addr}:{api_port}/system/configs/{cfg_name}")
    if res_status == 200:
        if "config_data" in config_data:
            return config_data["config_data"]
    return None


def send_api_command(url: str, content: dict = None) -> (int, dict):
    if not url.startswith("http"):
        url = "http://" + url

    response = None
    # print(f"Sending API command to '{url}'")
    if content:
        response = requests.post(url, json=content)
    else:
        response = requests.post(url)

    res_data = {}
    try:
        res_data = json.loads(response.content.decode())
    except json.decoder.JSONDecodeError:
        pass
    return response.status_code, res_data


def send_api_request(url: str) -> (int, dict):
    if not url.startswith("http"):
        url = "http://" + url

    # print(f"Sending API request to '{url}'")
    response = requests.get(url)
    res_data = {}
    try:
        res_data = json.loads(response.content.decode())
    except json.decoder.JSONDecodeError:
        pass
    return response.status_code, res_data


def read_socket_data_until(client: socket, print_lines: bool, filter_for_sender: Optional[str] = None,
                           exit_on_finish_code: bool = True) -> (bool, Optional[dict]):
    """
    Reads the socket data forever or untin a message with the status 0 is received

    :param client: Socket Object for the conection
    :param print_lines: Whether the received lines should be printed or not
    :param filter_for_sender: Use to only handle messages from a specific sender
    :param exit_on_finish_code: Whether to exit on status code 0
    :return: (Whether method run through successfully), (Last request received)
    """
    last_data_received: Optional[dict] = None
    try:
        while True:
            buf_rec_data = client.recv(5000).decode().strip("\n").strip("'").strip('"').strip()
            data: dict = {}

            rec_message: str = buf_rec_data
            rec_status: int = 0
            rec_sender: str = "???"

            try:
                data: dict = json.loads(buf_rec_data)
            except json.decoder.JSONDecodeError:
                rec_status = -1000

            if "sender" in data:
                rec_sender = data["sender"]

            if filter_for_sender and rec_sender != filter_for_sender:
                continue

            if "message" in data:
                rec_message = data["message"]

            if "status" in data:
                rec_status = data["status"]

            if print_lines:  # Print lines if wanted
                print(f'-> [{rec_sender}][{rec_status}]: {rec_message}')

            if "sender" in data or "status" in data:
                last_data_received = data
                if exit_on_finish_code:
                    if rec_status == 0:
                        break

    except KeyboardInterrupt:
        print("Forced Exit...")
        return False, last_data_received
    return True, last_data_received


def socket_connector(port: int, host: str, exit_on_failure: False) -> (bool, Optional[dict]):
    if host == "localhost":
        host = socket.gethostname()  # as both code is running on same pc

    try:
        client_socket = socket.socket()  # instantiate
        print(f"Connecting to {host}:{port}...")
        client_socket.connect((host, port))  # connect to the server
    except ConnectionRefusedError:
        print(f"Connection to {host}:{port} was refused")
        return False, ""
    print("Connected.")

    buf_res, last_data_received = read_socket_data_until(client_socket,
                                                         True,
                                                         exit_on_finish_code=exit_on_failure)

    client_socket.close()  # close the connection
    print("Connection Closed")
    return buf_res, last_data_received


def format_string_len(in_data: str, length: int) -> str:
    if not isinstance(in_data, str):
        in_data = str(in_data)
    return in_data + " " * (length - len(in_data))


def upload_software_to_client(serial_port: str) -> bool:
    print("Uploading Software to Client:")
    flasher = ChipFlasher()
    result = flasher.upload_software("develop", serial_port)

    if result:
        print("Uploading software was successful")
        return True
    else:
        print("Uploading software failed.")
        if ask_for_continue("Try again with some extra caution?"):
            print("Uploading Software to Client:")
            result = flasher.upload_software("develop", serial_port, clone_new_repository=True)

            if result:
                print("Uploading software was successful")
                return True
            else:
                print("Uploading software failed again.")
                return False
        else:
            return False


class ToolkitException(Exception):
    def __init__(self):
        super().__init__("ToolkitException")


class BridgeRestApiException(Exception):
    def __init__(self):
        super().__init__("An Error with the Bridge REST API occurred")


class BridgeSocketApiException(Exception):
    def __init__(self):
        super().__init__("An Error with the Socket API occurred")


class ClientDoesNotExistException(Exception):
    def __init__(self, name: str):
        super().__init__(f"No client named '{name}' was found")


class GadgetDoesNotExistException(Exception):
    def __init__(self, name: str):
        super().__init__(f"No gadget named '{name}' was found")


class BridgeConnector:
    _socket_client: socket.socket
    _logger: logging.Logger

    _connected: bool

    _address: str
    _rest_port: int
    _socket_port: int

    _bridge_name: str
    _running_since: str
    _git_branch: Optional[str]
    _git_commit: Optional[str]

    _clients: dict
    _connectors: dict
    _gadgets: dict
    _configs: dict
    _serial_ports: list

    def __init__(self, address, rest_port, socket_port):
        self._logger = logging.getLogger("BridgeConnector")
        self._socket_client = socket.socket()
        self._address = address
        self._rest_port = rest_port
        self._socket_port = socket_port
        self._connected = False

    def __del__(self):
        self._disconnect()

    def _send_api_request(self, url: str) -> (int, dict):
        if not url.startswith("http"):
            url = "http://" + url

        self._logger.info(f"Sending API request to '{url}'")
        response = requests.get(url)
        try:
            res_data = json.loads(response.content.decode())
        except json.decoder.JSONDecodeError:
            self._logger.error(f"Failed to parse received payload to json")
            return 1200, {}
        return response.status_code, res_data

    def _disconnect(self):
        self._logger.info("Closing all active connections")
        self._connected = False
        self._socket_client.close()

    def _fetch_data(self, path: str) -> Optional[dict]:
        full_path = f"{bridge_addr}:{api_port}/{path}"
        status, data = self._send_api_request(full_path)

        if status != 200:
            self._logger.error(f"Could not load information from the bridge at '{full_path}'")
            raise BridgeRestApiException

        return data

    def _load_info(self):
        self._logger.info("Fetching bridge info")
        bridge_info = self._fetch_data(f"info")

        self._bridge_name = bridge_info["bridge_name"]
        self._running_since = bridge_info["running_since"]
        self._git_branch = bridge_info["software_branch"]
        self._git_commit = bridge_info["software_commit"]

    def _load_configs(self):
        self._logger.info("Fetching client config data from bridge")
        config_name_data = self._fetch_data("system/configs")
        self._remote_configs = config_name_data["config_names"]

    def _load_clients(self):
        self._clients = {}
        client_data_res = self._fetch_data("clients")

        for client_data in client_data_res["clients"]:
            try:
                buf_name = client_data["name"]

                if buf_name in self._clients:
                    self._logger.error(f"Received data for two clients named '{buf_name}'")

                buf_client = {"boot_mode": client_data["boot_mode"],
                              "is_active": client_data["is_active"],
                              "sw_branch": client_data["sw_branch"],
                              "sw_version": client_data["sw_version"],
                              "sw_uploaded": client_data["sw_uploaded"]}

                self._clients[buf_name] = buf_client
            except KeyError:
                self._logger.error("A client property could not be loaded")

    def _load_gadgets(self):
        self._gadgets = {}
        gadget_data_res = self._fetch_data("gadgets")

        for gadget_data in gadget_data_res["gadgets"]:
            try:
                buf_name = gadget_data["name"]

                if buf_name in self._clients:
                    self._logger.error(f"Received data for two gadgets named '{buf_name}'")

                buf_gadget = {"type": gadget_data["type"],
                              "characteristics": gadget_data["characteristics"]}

                self._gadgets[buf_name] = buf_gadget
            except KeyError:
                self._logger.error("A gadget property could not be loaded")

    def _load_connectors(self):
        self._connectors = {}

    def _load_serial_ports(self):
        serial_port_data = self._fetch_data("system/get_serial_ports")
        self._serial_ports = serial_port_data["serial_ports"]

    def load_data(self):
        self._load_info()
        self._load_configs()
        self._load_clients()
        self._load_gadgets()
        self._load_connectors()
        self._load_serial_ports()

    def connect(self):
        self._disconnect()

        self._fetch_data("")
        self._logger.info("REST-API is responding")

        try:
            self._socket_client.connect((self._address, self._socket_port))  # connect to the server
        except ConnectionRefusedError:
            self._logger.error("Could not connect to remote socket")
            raise BridgeSocketApiException
        self._logger.info("Connected to the Socket API")

        self._connected = True

    def get_address(self) -> str:
        return self._address

    def get_rest_port(self) -> int:
        return self._rest_port

    def get_socket_port(self) -> int:
        return self._socket_port

    def get_name(self) -> str:
        return self._bridge_name

    def get_launch_time(self) -> str:
        return self._running_since

    def get_commit(self) -> str:
        return self._git_commit

    def get_branch(self) -> str:
        return self._git_branch

    def get_client_names(self) -> list:
        out_list = []
        for client_name in self._clients:
            out_list.append(client_name)
        return out_list

    def get_client_data(self, name: str) -> dict:
        try:
            return self._clients[name]
        except KeyError:
            raise ClientDoesNotExistException

    def get_gadget_names(self) -> list:
        out_list = []
        for gadget_name in self._gadgets:
            out_list.append(gadget_name)
        return out_list

    def get_gadget_data(self, name: str) -> dict:
        try:
            return self._gadgets[name]
        except KeyError:
            raise GadgetDoesNotExistException


class BridgeConnectionToolkit:
    _bridge_connector = BridgeConnector

    def __init__(self, bridge_ip, bridge_rest_port, bridge_websocket_port):
        self._bridge_connector = BridgeConnector(bridge_ip, bridge_rest_port, bridge_websocket_port)

    def _print_bridge_info(self):
        print(f"Status of '{}':")

    def run(self):
        print("Connecting to bridge...")
        try:
            self._bridge_connector.connect()
            print("Connection established.")
        except (BridgeRestApiException, BridgeSocketApiException):
            print("Connection could not be established")
            return


class DirectConnectionToolkit(metaclass=ABCMeta):
    _network: Optional[NetworkConnector]
    _client_name: Optional[str]

    def __init__(self):
        self._network = None
        self._client_name = None

    def __del__(self):
        if self._network:
            self._network.__del__()

    def run(self):
        """Runs the toolkit, accepting user inputs and executing the selcted tasks"""

        self._get_ready()

        self._connect_to_client()

        print("Connected to '{}'".format(self._client_name))

        while True:
            if not self._select_task():
                break

    def _select_task(self) -> bool:
        task_option = select_option(["Overwrite EEPROM", "Write Config", "Reboot"],
                                    "what to do",
                                    "Quit")

        if task_option == -1:
            return False

        elif task_option == 0:  # Overwrite EEPROM
            self._erase_config()
            return True

        elif task_option == 1:  # Write Config
            self._write_config()
            return True

        elif task_option == 2:  # Reboot
            self._reboot_client()
            print("Reconnecting might be required.")
            return True

    def _erase_config(self):
        print()
        print("Overwriting EEPROM:")

        erase_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            ack = erase_controller.reset_config()
            if ack is False:
                print("Failed to reset EEPROM\n")
                return

            print("Config was successfully erased\n")

        except NoClientResponseException:
            print("Received no Response to Reset Request\n")
            return

    def _write_config(self):

        manager = ClientConfigManager()
        config_names = manager.get_config_names()

        config_path: Optional[str]
        config_data: Optional[dict] = None

        while not config_data:

            config_index = select_option(config_names,
                                         "which config to write",
                                         "Quit")

            if config_index == -1:
                return

            config_data = manager.get_config(config_names[config_index])

            if not config_data:
                response = ask_for_continue("Config file could either not be loaded, isn no valid json file or"
                                            "no valid config. Try again?")
                if not response:
                    return
                else:
                    continue

        print(f"Loaded config '{config_data['name']}'")
        print()
        print("Writing config:")

        write_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            with LoadingIndicator():
                ack = write_controller.write_config(config_data)
            if ack is False:
                print("Failed to write config\n")
                return

            print("Config was successfully written\n")

        except NoClientResponseException:
            print("Received no response to config write request\n")
            return

    def _reboot_client(self):
        print()
        print("Rebooting Client:")

        reboot_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            with LoadingIndicator():
                ack = reboot_controller.reboot_client()
            if ack is False:
                print("Failed to reboot client\n")
                return

            print("Client reboot successful\n")

        except NoClientResponseException:
            print("Received no response to reboot request\n")
            return

    def _connect_to_client(self):
        """Scans for clients and lets the user select one if needed and possible."""
        while not self._client_name:

            with LoadingIndicator():
                client_id = None
                client_list = self._scan_for_clients()

                if len(client_list) == 0:
                    print("No client answered to broadcast")
                elif len(client_list) > 1:
                    client_id = select_option(client_list, "client to connect to")
                else:
                    client_id = client_list[0]
                self._client_name = client_id

            if not self._client_name:
                response = ask_for_continue("Could not find any gadget. Try again?")
                if not response:
                    raise ToolkitException

    @abstractmethod
    def _get_ready(self):
        pass

    @abstractmethod
    def _scan_for_clients(self) -> [str]:
        """Sends a broadcast and waits for clients to answer.

        Returns a list containing the names of all available clients."""
        pass


class DirectSerialConnectionToolkit(DirectConnectionToolkit):

    _serial_port: str

    def __init__(self, serial_port: str):
        super().__init__()
        self._serial_port = serial_port
        self._network = SerialConnector(TOOLKIT_NETWORK_NAME,
                                        self._serial_port,
                                        115200)

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        print("Waiting for Clients to boot up")

        with LoadingIndicator():
            time.sleep(5)

        print("Please make sure your Client is connected to this machine and can receive serial requests")

    def _scan_for_clients(self) -> [str]:
        req = Request("smarthome/broadcast/req",
                      gen_req_id(),
                      TOOLKIT_NETWORK_NAME,
                      None,
                      {})

        responses = self._network.send_broadcast(req)

        client_names = []
        for broadcast_res in responses:
            client_names.append(broadcast_res.get_sender())

        return client_names


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

        self._network = MQTTConnector("ConsoleToolkit",
                                      self._mqtt_ip,
                                      self._mqtt_port,
                                      self._mqtt_username,
                                      self._mqtt_password)
        pass

    def __del__(self):
        super().__del__()

    def _get_ready(self):
        print("Please make sure your Client is connected to the network")

    def _scan_for_clients(self) -> [str]:
        req = Request("smarthome/broadcast/req",
                      gen_req_id(),
                      TOOLKIT_NETWORK_NAME,
                      None,
                      {})

        responses = self._network.send_broadcast(req)

        client_names = []
        for broadcast_res in responses:
            client_names.append(broadcast_res.get_sender())

        return client_names


if __name__ == '__main__':
    # Argument-parser
    parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
    parser.add_argument('--connection_mode',
                        help='Use "bridge" to connect to bridge or "direct" to connect to chip directly',
                        type=str)
    parser.add_argument('--bridge_socket_port', help='[Bridge] Port of the Socket Server', type=int)
    parser.add_argument('--bridge_api_port', help='[Bridge] Port of the Socket Server', type=int)
    parser.add_argument('--bridge_addr', help='[Bridge] Address of the Socket Server', type=str)
    parser.add_argument('--serial_port', help='[Direct] Name of the serial port to use', type=str)
    parser.add_argument('--mqtt_ip', help='[Direct] IP of the MQTT broker', type=str)
    parser.add_argument('--mqtt_port', help='[Direct] Port of the MQTT broker', type=int)
    parser.add_argument('--mqtt_user', help='[Direct] Username to access the MQTT broker', type=str)
    parser.add_argument('--mqtt_pw', help='[Direct] Password to access the MQTT broker', type=str)
    parser.add_argument('--debug', help='Activates the Debug Logger', action='store_true')
    ARGS = parser.parse_args()

    print("Launching...")

    if ARGS.debug:
        print("Activated Debug Logging")
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if ARGS.connection_mode:
        connection_mode = ARGS.connection_mode
    else:
        connection_mode = select_option(["Bridge", "Direct", "Upload Software"], "Connection Mode", "Quit")
        if connection_mode == -1:
            sys.exit(0)

    if connection_mode == 0:  # Bridge

        socket_client: socket = None

        if ARGS.bridge_addr:
            bridge_addr = ARGS.bridge_addr
        else:
            bridge_addr = input("Please enter server address: ")

        if ARGS.bridge_socket_port:
            socket_port = ARGS.bridge_socket_port
        else:
            try:
                socket_port = int(input("Please enter server socket port: "))
            except ValueError:
                print("Illegal port.")
                sys.exit(1)

        if ARGS.bridge_api_port:
            api_port = ARGS.bridge_api_port
        else:
            try:
                api_port = int(input("Please enter server API port: "))
            except ValueError:
                print("Illegal port.")
                sys.exit(1)

        print("Connecting to bridge...")
        status, _ = send_api_request(f"{bridge_addr}:{api_port}")
        if status == 200:
            print("Connected to API")
        else:
            print("API could not be reached")
            sys.exit(2)

        buf_bridge_addr = bridge_addr
        if bridge_addr == "localhost":
            buf_bridge_addr = socket.gethostname()

        try:
            socket_client = socket.socket()
            socket_client.connect((buf_bridge_addr, socket_port))  # connect to the server
        except ConnectionRefusedError:
            print(f"Connection to {buf_bridge_addr}:{socket_port} was refused")
            sys.exit(3)
        print("Connected to Bridge Socket")

        status, bridge_data = send_api_request(f"{bridge_addr}:{api_port}/info")
        if status != 200:
            print("Could not load information from the bridge.")
            sys.exit(4)

        # Serial Ports available on the bridge
        bridge_serial_ports = []
        detected_serial_ports = read_serial_ports_from_bridge()
        if detected_serial_ports:
            bridge_serial_ports = ["default"] + detected_serial_ports
        del detected_serial_ports

        # Configs stored on the bridge
        bridge_configs = read_configs_from_bridge()

        # Configs found locally
        local_configs = []

        print()
        print("Connected to bridge '{}'".format(bridge_data["bridge_name"]))
        print(" -> Running since: {}".format(bridge_data["running_since"]))
        print(" -> Software Branch: {}".format(bridge_data["software_branch"]))
        print(" -> Software Commit: {}".format(bridge_data["software_commit"]))
        print(" -> Clients: {}".format(bridge_data["client_count"]))
        print(" -> Connectors: {}".format(bridge_data["connector_count"]))
        print(" -> Gadgets: {}".format(bridge_data["gadget_count"]))

        bridge_clients: [dict] = []
        client_max_name_len = 0
        client_max_branch_name_len = 0

        bridge_gadgets: [dict] = []
        gadget_max_name_len = 0

        status, client_data = send_api_request(f"{bridge_addr}:{api_port}/clients")

        if status != 200:
            print("Could not load clients from the bridge.")
            sys.exit(5)

        for client_data in client_data["clients"]:
            try:
                buf_client = {"boot_mode": client_data["boot_mode"],
                              "name": client_data["name"],
                              "is_active": client_data["is_active"],
                              "sw_branch": client_data["sw_branch"] if client_data["sw_branch"] else "unknown",
                              "sw_version": client_data["sw_version"] if client_data["sw_version"] else "unknown",
                              "sw_uploaded": client_data["sw_uploaded"] if client_data["sw_uploaded"] else "unknown"}

                # determine the maximum lengths of name & branch for displaying them
                name_len = len(buf_client["name"])
                branch_len = len(buf_client["sw_branch"])

                if name_len > client_max_name_len:
                    client_max_name_len = name_len

                if branch_len > client_max_branch_name_len:
                    client_max_branch_name_len = branch_len

                bridge_clients.append(buf_client)
            except KeyError:
                print("A client property could not be loaded")

        client_names: [str] = []

        print()
        print("Clients loaded:")
        for client_data in bridge_clients:
            c_name = client_data["name"]
            c_commit = client_data["sw_version"][:7]
            c_branch = client_data["sw_branch"]

            client_names.append(c_name)
            client_pattern = " -> {}  |  Commit: {}  |  Branch: {}  |  {}"
            print(client_pattern.format(
                format_string_len(client_data["name"], client_max_name_len),
                c_commit,
                format_string_len(c_branch, client_max_branch_name_len),
                ("Active" if client_data["is_active"] else "Inactive")
            ))

        status, gadget_data = send_api_request(f"{bridge_addr}:{api_port}/gadgets")

        if status != 200:
            print("Could not load gadgets from the bridge.")
            sys.exit(5)

        for gadget_data in gadget_data["gadgets"]:
            try:
                buf_gadget = {"type": gadget_data["type"],
                              "name": gadget_data["name"],
                              "characteristics": gadget_data["characteristics"]}

                name_len = len(buf_gadget["name"])

                if name_len > gadget_max_name_len:
                    gadget_max_name_len = name_len

                bridge_gadgets.append(buf_gadget)
            except KeyError:
                print("A gadget property could not be loaded")

        print()
        print("Gadgets loaded:")
        for gadget_data in bridge_gadgets:
            print(" -> {} <{}>".format(
                format_string_len(gadget_data["name"], gadget_max_name_len),
                gadgetlib.gadget_identifier_to_str(GadgetIdentifier(gadget_data["type"]))
            ))

            characteristic_max_len = 0
            for characteristic_data in gadget_data["characteristics"]:
                name = gadgetlib.characteristic_identifier_to_str(CharacteristicIdentifier(characteristic_data["type"]))
                if len(name) > characteristic_max_len:
                    characteristic_max_len = len(name)

            for characteristic_data in gadget_data["characteristics"]:
                characteristic_display = ""
                value_display = characteristic_data["value"]

                if characteristic_data["min"] == 0 and characteristic_data["max"] == 1:
                    if characteristic_data["value"] == 1:
                        value_display = "On"
                    else:
                        value_display = "Off"

                characteristic_display = "{} | {} | {}".format(
                    format_string_len(characteristic_data["min"], 3),
                    format_string_len(value_display, 3),
                    format_string_len(characteristic_data["max"], 3)
                )

                char_ident = CharacteristicIdentifier(characteristic_data["type"])

                print("       {} : {}".format(
                    format_string_len(gadgetlib.characteristic_identifier_to_str(char_ident), characteristic_max_len),
                    characteristic_display
                ))
            print()

        keep_running = True

        while keep_running:
            print()
            task_option = select_option(BRIDGE_FUNCTIONS, None, "Quit")

            if task_option == 0:
                # Write software to chip
                selected_branch = select_option(DEFAULT_SW_BRANCH_NAMES, "Branch", "Back")
                selected_branch_name = ""
                if selected_branch == 0:
                    selected_branch_name = input("Enter branch name:")
                elif selected_branch == -1:
                    continue
                else:
                    selected_branch_name = DEFAULT_SW_BRANCH_NAMES[selected_branch]
                print(f"Writing software branch '{selected_branch_name}':")

                sel_ser_port = 0
                sel_ser_port_str = ""
                if bridge_serial_ports:
                    sel_ser_port = select_option(bridge_serial_ports, "Serial Port for Upload", "Back")
                    if sel_ser_port == -1:
                        continue
                    sel_ser_port_str = bridge_serial_ports[sel_ser_port]

                serial_port_option = f'&serial_port={sel_ser_port_str}' if sel_ser_port else ''
                flash_path = f"/system/flash_software?branch_name={selected_branch_name}{serial_port_option}"

                status, resp_data = send_api_command(f"{bridge_addr}:{api_port}{flash_path}")
                if status != 200:
                    print(f"Software flashing could no be started:\n{resp_data}")
                    continue

                # Read lines from socket port
                success, last_data = read_socket_data_until(socket_client,
                                                            True,
                                                            "SOFTWARE_UPLOAD")

                if not success:
                    print("Unknown error or interruption while reading socket data")
                    continue

                if last_data["status"] == 0:  # TODO: make use of new status codes
                    print("Flashing Software was successful")
                else:
                    print("Flashing Software failed")

            elif task_option == 1:
                # Write config to chip
                flash_mode = select_option(CONFIG_FLASH_OPTIONS, "Chip Connection", "Back")
                if flash_mode == -1:
                    continue

                # Configs stored on the bridge
                bridge_configs = read_configs_from_bridge()

                config_index = select_option(["Custom Config"] + bridge_configs, "Config", "Back")
                config_to_flash = None

                if config_index == -1:
                    continue
                elif config_index == 0:
                    print("Custom Config not implemented")
                    continue
                else:
                    config_name = bridge_configs[config_index-1]
                    config_to_flash = read_config_from_bridge(config_name)

                if not config_to_flash:
                    print("Error: Unable to load config from bridge.")
                    continue

                if flash_mode == 0:
                    print(f"Writing config to chip connected via USB...")

                    sel_ser_port = 0
                    sel_ser_port_str = ""
                    if bridge_serial_ports:
                        sel_ser_port = select_option(bridge_serial_ports, "Serial Port for Upload", "Back")
                        if sel_ser_port == -1:
                            continue

                        sel_ser_port_str = bridge_serial_ports[sel_ser_port]

                    serial_port_option = f'?serial_port={sel_ser_port_str}' if sel_ser_port else ''

                    flash_path = f"/system/write_config{serial_port_option}"

                    status, resp_data = send_api_command(f"{bridge_addr}:{api_port}{flash_path}", config_to_flash)
                    if status != 200:
                        if "status" in resp_data:
                            print(f"Writing config could no be started:\n{resp_data['status']}")
                        else:
                            print(f"Writing config could no be started.")
                        continue

                    # Read lines from socket port
                    success, last_data = read_socket_data_until(socket_client,
                                                                True,
                                                                "CONFIG_UPLOAD")

                else:
                    print(f"Writing config to chip connected via Wifi...")
                    selected_chip_nr = select_option(client_names, "Chip", "Back")
                    if selected_chip_nr == -1:
                        continue
                    selected_cip = client_names[selected_chip_nr]
                    print(f"Writing config to '{selected_cip}'...")

                    flash_path = f"/clients/{selected_cip}/write_config"
                    status, resp_data = send_api_command(f"{bridge_addr}:{api_port}{flash_path}", config_to_flash)
                    if status != 200:
                        if "status" in resp_data:
                            print(f"Writing config could no be started:\n{resp_data['status']}")
                        else:
                            print(f"Writing config could no be started.")
                        continue

                        # Read lines from socket port
                    success, last_data = read_socket_data_until(socket_client,
                                                                True,
                                                                "CONFIG_UPLOAD")

            elif task_option == 2:
                # restart client
                selected_cip = client_names[select_option(client_names, "Chip")]
                print(f"Restarting client '{selected_cip}'...")

            elif task_option == 3:
                # Update Toolkit
                update_status = git_tools.update()
                if update_status:
                    print("Restart?")
                    restart_bridge = select_option(["Yes", "No"]) == 0
                    if restart_bridge:
                        print("Restarting...")
                        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

            elif task_option == -1:
                # Quit
                print(f"Quitting...")
                sys.exit(0)

    elif connection_mode == 1:  # Direct
        toolkit_instance: DirectConnectionToolkit
        if ARGS.serial_port:
            print("Using serial port provided by program argument")
            try:
                toolkit_instance = DirectSerialConnectionToolkit(ARGS.serial_port)
            except ToolkitException:
                sys.exit(1)

        elif ARGS.mqtt_ip and ARGS.mqtt_port:
            print("Using mqtt config provided by program argument")
            username = None
            password = None
            if ARGS.mqtt_user:
                username = ARGS.mqtt_user
            if ARGS.mqtt_pw:
                password = ARGS.mqtt_pw
            try:
                toolkit_instance = DirectMqttConnectionToolkit(
                    ARGS.mqtt_ip,
                    ARGS.mqtt_port,
                    username,
                    password
                )
            except ToolkitException:
                sys.exit(1)
        else:
            print("How do you want to connect to the Client?")
            connection_type = select_option(["serial", "mqtt"], "how to connect to the Client", "Quit")

            if connection_type == -1:  # Quit
                sys.exit(0)

            if connection_type == 0:  # Serial
                serial_ports = ChipFlasher.get_serial_ports()
                serial_port_index = connection_type = select_option(serial_ports, "Serial Port", "Quit")
                if serial_port_index == -1:
                    sys.exit(0)
                serial_port = serial_ports[serial_port_index]

                try:
                    toolkit_instance = DirectSerialConnectionToolkit(serial_port)
                except ToolkitException:
                    sys.exit(1)

            elif connection_type == 1:  # MQTT
                manager = ToolkitSettingsManager()
                selected_config: Optional[dict] = None

                while selected_config is None:
                    config_ids = manager.get_mqtt_config_ids()
                    config_id = select_option(config_ids + ["Create New Config"], "a config", "Quit")

                    if config_id == -1:  # Quit
                        sys.exit(0)

                    elif config_id == len(config_ids):
                        ip = input("Please enter the IP Address of the MQTT Broker\n")
                        port = int(input("Please enter the Port of the MQTT Broker\n"))

                        username = input("Please enter the Username of the MQTT Broker. "
                                         "Leave Empty if there isn't any.\n")

                        if username:
                            password = input("Please enter the Password of the MQTT Broker. "
                                             "Leave Empty if there isn't any.\n")
                            if not password:
                                password = None
                        else:
                            username = None
                            password = None

                        config_name = input("Please enter a ID to identify the config later\n")
                        override = False

                        while len(config_name) < 3 or (config_name in config_ids and not override):
                            if len(config_name) < 3:
                                print("The config ID has to be at least 3 Chars long")
                                config_name = input("Please enter a ID to identify the config later\n")
                                continue

                            print("A config with this name already exists, what do you want to do?")
                            to_do = select_option(config_ids + ["Override", "Select new ID"], "what to do", "Quit")

                            if to_do == -1:  # Quit
                                sys.exit(0)
                            elif to_do == 0:  # Override
                                override = True
                            else:
                                config_name = input("Please enter a ID to identify the config later\n")

                        print(f"You entered the following config:\n"
                              f"ID: {config_name}\n"
                              f"IP: {ip}\n"
                              f"Port: {port}\n"
                              f"Username: {username}\n"
                              f"Password: {password}")

                        if not ask_for_continue("Do you want to use it?"):
                            continue

                        try:
                            manager.set_mqtt_config(config_name,
                                                    {"ip": ip,
                                                     "port": port,
                                                     "username": username,
                                                     "password": password})
                        except InvalidConfigException:
                            print("Some of the entered values were illegal, please try again.\n")
                            continue

                        if ask_for_continue("Do you want to save all created configs?"):
                            manager.save()
                    else:
                        selected_config = manager.get_mqtt_config(config_ids[config_id])

                try:
                    toolkit_instance = DirectMqttConnectionToolkit(selected_config["ip"],
                                                                   selected_config["port"],
                                                                   selected_config["username"],
                                                                   selected_config["password"])
                except ToolkitException:
                    sys.exit(1)

            else:  # Error
                sys.exit(1)

        try:
            toolkit_instance.run()
            toolkit_instance.__del__()
        except ToolkitException:
            toolkit_instance.__del__()
            sys.exit(1)

    elif connection_mode == 2:  # Direct - Upload Software
        serial_port: str = ""
        if ARGS.serial_port:
            serial_port = ARGS.serial_port
        else:
            serial_ports = ChipFlasher.get_serial_ports()
            serial_port_index = connection_type = select_option(serial_ports, "Serial Port", "Quit")
            if serial_port_index == -1:
                sys.exit(0)
            serial_port = serial_ports[serial_port_index]
        upload_software_to_client(serial_port)

    print("Quitting...")
