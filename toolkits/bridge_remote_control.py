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
from jsonschema import validate, ValidationError
from abc import ABCMeta, abstractmethod
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier
from typing import Optional
from tools import git_tools
from serial_connector import SerialConnector
from mqtt_connector import MQTTConnector
from network_connector import NetworkConnector, Request
from chip_flasher import get_serial_ports, flash_chip

TOOLKIT_NETWORK_NAME = "ConsoleToolkit"
TOOLKIT_DIRECT_TASK_OPTIONS = ["Overwrite EEPROM", "Write Config"]

CONNECTION_MODES = ["direct", "bridge"]
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


def load_config(path: str) -> Optional[dict]:
    """Loads a config from the disk and validates it. Returns None on Error."""
    try:
        json_schema: dict = {}
        with open(os.path.join("json_schemas", "client_config.json")) as file_h:
            json_schema = json.load(file_h)
        with open(path) as file_h:
            config_data = json.load(file_h)
            validate(config_data, json_schema)
            return config_data
    except (OSError, IOError, ValidationError):
        return None


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
        except TypeError:
            selection = None

        if selection < 0 or selection > max_i:
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


class ToolkitException(Exception):
    def __init__(self):
        super().__init__("ToolkitException")


class DirectConnectionToolkit(metaclass=ABCMeta):
    _client: Optional[NetworkConnector]
    _client_name: Optional[str]

    def __init__(self):
        self._client = None
        self._client_name = None

    def __del__(self):
        if self._client:
            self._client.__del__()

    def run(self):
        # Wait for all chips to be alive

        print("Waiting for Clients to boot up")
        load = LoadingIndicator()
        load.run()
        time.sleep(5)
        load.stop()

        print("Please make sure your chip can receive serial requests")
        while not self._client_name:
            load.run()
            self._client_name = self._connect_to_client()
            load.stop()
            if not self._client_name:
                response = ask_for_continue("Could not find any gadget. Try again?")
                if not response:
                    return

        while True:

            print("Connected to '{}'".format(self._client_name))

            task_option = select_option(TOOLKIT_DIRECT_TASK_OPTIONS, "what to do", "Quit")

            if task_option == -1:
                break

            elif task_option == 0:  # Overwrite EEPROM
                self._erase_config()
                continue

            elif task_option == 1:  # Write Config
                self._write_config()
                continue

    def _erase_config(self):
        print()
        print("Overwriting EEPROM:")

        reset_req = Request("smarthome/config/reset",
                            gen_req_id(),
                            TOOLKIT_NETWORK_NAME,
                            self._client_name,
                            {"reset_option": "erase"})

        (ack, res) = self._client.send_request(reset_req)

        if ack is None:
            print("Received no Response to Reset Request\n")
            return

        if ack is False:
            print("Failed to reset EEPROM\n")
            return

        print("Config was successfully erased\n")

    def _write_config(self):
        config_path: Optional[str]
        config_data: Optional[dict] = None
        while not config_data:
            config_path = enter_file_path()
            if not config_path:
                response = ask_for_continue("Entered invalid config path. Try again?")
                if not response:
                    return
                else:
                    continue

            config_data = load_config(config_path)
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
        config_req = Request("smarthome/config/write",
                             gen_req_id(),
                             TOOLKIT_NETWORK_NAME,
                             self._client_name,
                             {"config": config_data})
        load = LoadingIndicator()
        load.run()
        (ack, res) = self._client.send_request_split(config_req, timeout=15)
        load.stop()

        if ack is None:
            print("Received no Response to write Config Request\n")
            return

        if ack is False:
            print("Failed to write Config\n")
            return

        print("Config was successfully written\n")

    def _connect_to_client(self) -> Optional[str]:
        """Scans for clients and lets the user select one if needed and possible."""

        client_id = None
        client_list = self._scan_for_clients()

        if len(client_list) == 0:
            print("No client answered to broadcast")
        elif len(client_list) > 1:
            client_id = select_option(client_list, "client to connect to")
        else:
            client_id = client_list[0]
        return client_id

    @abstractmethod
    def _scan_for_clients(self) -> [str]:
        """Sends a broadcast and waits for clients to answer"""
        pass


class DirectSerialConnectionToolkit(DirectConnectionToolkit):

    _serial_port: str

    def __init__(self, serial_port: str):
        super().__init__()
        self._serial_port = serial_port
        self._client = SerialConnector(TOOLKIT_NETWORK_NAME,
                                       self._serial_port,
                                       115200)

    def __del__(self):
        super().__del__()

    def _scan_for_clients(self) -> [str]:
        req = Request("smarthome/broadcast/req",
                      gen_req_id(),
                      TOOLKIT_NETWORK_NAME,
                      None,
                      {})

        responses = self._client.send_broadcast(req)

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

        self._client = MQTTConnector("ConsoleToolkit",
                                     self._mqtt_ip,
                                     self._mqtt_port,
                                     self._mqtt_username,
                                     self._mqtt_password)
        pass

    def __del__(self):
        super().__del__()

    def _scan_for_clients(self) -> [str]:
        req = Request("smarthome/broadcast/req",
                      gen_req_id(),
                      TOOLKIT_NETWORK_NAME,
                      None,
                      {})

        responses = self._client.send_broadcast(req)

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
        connection_mode_nr = select_option(CONNECTION_MODES, "Connection Mode", "Quit")
        if connection_mode_nr == -1:
            sys.exit(0)
        connection_mode = CONNECTION_MODES[connection_mode_nr]

    if connection_mode == "bridge":

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

    elif connection_mode == "direct":
        toolkit_instance: DirectConnectionToolkit
        if ARGS.serial_port:
            print("Using serial port provided by program argument")
            try:
                toolkit_instance = DirectSerialConnectionToolkit(ARGS.serial_port)
            except ToolkitException:
                sys.exit(1)

        elif ARGS.mqtt_ip:
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
                serial_ports = get_serial_ports()
                serial_port_index = connection_type = select_option(serial_ports, "Serial Port", "Quit")
                if serial_port_index == -1:
                    sys.exit(0)
                serial_port = serial_ports[serial_port_index]

                try:
                    toolkit_instance = DirectSerialConnectionToolkit(serial_port)
                except ToolkitException:
                    sys.exit(1)

            elif connection_type == 1:  # MQTT
                ip = input("Please enter the IP Address of the MQTT Broker\n")
                port = int(input("Please enter the Port of the MQTT Broker\n"))

                username = input("Please enter the Username of the MQTT Broker. Leave Empty if there isn't any.\n")

                if username:
                    password = input("Please enter the Password of the MQTT Broker. Leave Empty if there isn't any.\n")
                    if not password:
                        password = None
                else:
                    username = None
                    password = None

                try:
                    toolkit_instance = DirectMqttConnectionToolkit(ip, port, username, password)
                except ToolkitException:
                    sys.exit(1)

            else:  # Error
                sys.exit(1)

        try:
            toolkit_instance.run()
            toolkit_instance.__del__()
        except ToolkitException:
            sys.exit(1)

    print("Quitting...")
