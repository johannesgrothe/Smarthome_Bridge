import os
import socket
import argparse
import sys

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
from network.serial_connector import SerialConnector
from network.mqtt_connector import MQTTConnector
from network.network_connector import NetworkConnector, Request
from network.request import NoClientResponseException
from loading_indicator import LoadingIndicator
from chip_flasher import ChipFlasher
from client_controller import ClientController
from client_config_manager import ClientConfigManager
from toolkit_settings_manager import ToolkitSettingsManager, InvalidConfigException
from bridge_connector import BridgeConnector, BridgeSocketApiException, BridgeRestApiException,\
    SoftwareWritingFailedException, ConfigWritingFailedException

TOOLKIT_NETWORK_NAME = "ConsoleToolkit"

DIRECT_NETWORK_MODES = ["serial", "mqtt"]
BRIDGE_FUNCTIONS = ["Write software to chip", "Write config to chip", "Reboot chip", "Update Toolkit"]
DEFAULT_SW_BRANCH_NAMES = ["Enter own branch name", "master", "develop"]
CONFIG_FLASH_OPTIONS = ["Direct", "Wifi"]


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


_unknown_data_replacement = "unknown"
_default_git_branches = ["master", "develop"]


class BridgeConnectionToolkit:
    _bridge_connector: BridgeConnector
    _logger: logging.Logger

    _client_name_len_max: int
    _client_branch_name_len_max: int
    _gadget_name_len_max: int

    _tasks = list

    def __init__(self, bridge_ip, bridge_rest_port, bridge_websocket_port):
        self._bridge_connector = BridgeConnector(bridge_ip, bridge_rest_port, bridge_websocket_port)
        self._logger = logging.getLogger("BridgeConnectionToolkit")
        self._tasks = [("Write Software to Client", self._write_software),
                       ("Write Config to Client", self._write_config),
                       ("Restart Client", self._restart_client)]

    def _select_config(self) -> Optional[dict]:
        manager = ClientConfigManager()
        config_names = manager.get_config_names()

        config_data: Optional[dict] = None

        while not config_data:

            config_index = select_option(config_names,
                                         "which config to write",
                                         "Quit")

            if config_index == -1:
                return None

            config_data = manager.get_config(config_names[config_index])

            if not config_data:
                response = ask_for_continue("Config file could either not be loaded, isn no valid json file or"
                                            "no valid config. Try again?")
                if not response:
                    return None
                else:
                    continue

            return config_data

    def _select_serial_port(self) -> Optional[str]:
        bridge_serial_ports = self._bridge_connector.get_serial_ports()
        if bridge_serial_ports:
            sel_ser_port = select_option(bridge_serial_ports, "Serial Port for Upload", "Back")
            if sel_ser_port == -1:
                return None
            return bridge_serial_ports[sel_ser_port]
        return None

    def _get_gadgets_max_name_length(self) -> int:
        gadget_max_name_len = 0

        for client_name in self._bridge_connector.get_gadget_names():
            name_len = len(client_name)
            if name_len > gadget_max_name_len:
                gadget_max_name_len = name_len

        return gadget_max_name_len

    def _get_clients_max_name_length(self) -> int:
        client_max_name_len = 0

        for client_name in self._bridge_connector.get_client_names():
            name_len = len(client_name)
            if name_len > client_max_name_len:
                client_max_name_len = name_len

        return client_max_name_len

    def _get_clients_max_branch_name_length(self) -> int:
        client_max_branch_name_len = len(_unknown_data_replacement)

        for client_name in self._bridge_connector.get_client_names():
            client_data = self._bridge_connector.get_client_data(client_name)
            if client_data["sw_branch"]:
                branch_len = len(client_data["sw_branch"])

                if branch_len > client_max_branch_name_len:
                    client_max_branch_name_len = branch_len

        return client_max_branch_name_len

    @staticmethod
    def _get_characteristics_name_len_max(characteristics: dict):
        characteristic_max_len = 0

        for characteristic_data in characteristics:
            name = gadgetlib.characteristic_identifier_to_str(CharacteristicIdentifier(characteristic_data["type"]))
            if len(name) > characteristic_max_len:
                characteristic_max_len = len(name)

        return characteristic_max_len

    def _refresh_bridge_data(self):
        self._bridge_connector.load_data()
        self._client_name_len_max = self._get_clients_max_name_length()
        self._client_branch_name_len_max = self._get_clients_max_branch_name_length()
        self._gadget_name_len_max = self._get_gadgets_max_name_length()

    def _print_bridge_info(self):
        print(f" -> Running since: {self._bridge_connector.get_launch_time()}")
        print(f" -> Software Branch: {self._bridge_connector.get_branch()}")
        print(f" -> Software Commit: {self._bridge_connector.get_commit()[:7]}")
        print(f" -> Clients: {len(self._bridge_connector.get_client_names())}")
        print(f" -> Connectors: {len(self._bridge_connector.get_connector_types())}")
        print(f" -> Gadgets: {len(self._bridge_connector.get_gadget_names())}")

    def _print_clients(self):
        for client_name in self._bridge_connector.get_client_names():
            client_data = self._bridge_connector.get_client_data(client_name)
            self._print_client(client_name, client_data)

    def _print_client(self, name: str, data: dict):
        if data["sw_version"]:
            c_commit = data["sw_version"][:7]
        else:
            c_commit = _unknown_data_replacement

        if data["sw_branch"]:
            c_branch = data["sw_branch"]
        else:
            c_branch = _unknown_data_replacement

        client_pattern = " -> {}  |  Commit: {}  |  Branch: {}  |  {}"
        print(client_pattern.format(
            format_string_len(name, self._client_name_len_max),
            c_commit,
            format_string_len(c_branch, self._client_branch_name_len_max),
            ("Active" if data["is_active"] else "Inactive")
        ))

    def _print_gadgets(self):
        for gadget_name in self._bridge_connector.get_gadget_names():
            gadget_data = self._bridge_connector.get_gadget_data(gadget_name)
            self._print_gadget(gadget_name, gadget_data)

    def _print_gadget(self, name: str, data: dict):
        print(" -> {} <{}>".format(
            format_string_len(name, self._gadget_name_len_max),
            gadgetlib.gadget_identifier_to_str(GadgetIdentifier(data["type"]))
        ))

        characteristic_max_len = self._get_characteristics_name_len_max(data["characteristics"])

        for characteristic_data in data["characteristics"]:
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

    @staticmethod
    def _software_write_callback(data: dict):
        print(f" -> {data['message']}")

    def _write_software(self):
        selected_branch = select_option(_default_git_branches + ["Enter own name"], "Branch", "Back")

        if selected_branch == -1:
            return
        elif selected_branch == len(_default_git_branches):
            selected_branch_name = input("Enter branch name:\n")
        else:
            selected_branch_name = _default_git_branches[selected_branch]
        print(f"Writing software branch '{selected_branch_name}':")

        serial_port = self._select_serial_port()
        if not serial_port:
            print("\nNo serial port available, quitting.")
            return

        try:
            self._bridge_connector.write_software_to_client(selected_branch_name,
                                                            serial_port,
                                                            self._software_write_callback)
            print("\nSoftware writing successful.")
        except SoftwareWritingFailedException:
            print("\nFailed to write software to client.")

    def _write_config_to_client(self, name: str, config: dict):
        try:
            self._bridge_connector.write_config_to_network_client(name, config, self._software_write_callback)
            print("\nConfig writing successful.")
        except ConfigWritingFailedException:
            print("\nFailed to write the config to the client.")

    def _write_config_to_serial(self, serial_port: str, config: dict):
        try:
            self._bridge_connector.write_config_to_serial_client(config, serial_port, self._software_write_callback)
            print("\nConfig writing successful.")
        except ConfigWritingFailedException:
            print("\nFailed to write the config to the client.")

    def _write_config(self):

        config = self._select_config()
        if not config:
            return

        client_names = self._bridge_connector.get_client_names()
        task_option = select_option(client_names + ["<Serial Connection>"],
                                    "where to write the config", "Back")
        if task_option == -1:
            return
        elif task_option == len(client_names):
            serial_port = self._select_serial_port()
            if not serial_port:
                print("\nNo serial port available, quitting.")
                return
            try:
                self._bridge_connector.write_config_to_serial_client(
                    config,
                    serial_port,
                    self._software_write_callback)
                print("\nConfig writing successful.")
            except ConfigWritingFailedException:
                print("\nFailed to write the config to the client.")
        else:
            client_name = client_names[task_option]
            try:
                self._bridge_connector.write_config_to_network_client(
                    client_name,
                    config,
                    self._software_write_callback)
                print("\nConfig writing successful.")
            except ConfigWritingFailedException:
                print("\nFailed to write the config to the client.")

    def _restart_client(self):
        print("restarting client")

    def _run_tasks(self):
        title_list = [x for (x, y) in self._tasks]
        method_list = [y for (x, y) in self._tasks]
        while True:
            print()
            task_option = select_option(title_list, "what to do", "Quit")
            if task_option == -1:
                return
            method_list[task_option]()

    def run(self):
        print("Connecting to bridge...")
        try:
            self._bridge_connector.connect()
            print("Connection established.")
        except (BridgeRestApiException, BridgeSocketApiException):
            print("Connection could not be established")
            return

        try:
            self._refresh_bridge_data()
            print(f"Connected to '{self._bridge_connector.get_name()}'")
            print()
            print("Status:")
            self._print_bridge_info()
            print()
            print("Clients:")
            self._print_clients()
            print()
            print("Gadgets:")
            self._print_gadgets()

            self._run_tasks()
        except BridgeRestApiException:
            print("Error fetching information about bridge")
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

        keep_running = True  # TODO: add to class

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
