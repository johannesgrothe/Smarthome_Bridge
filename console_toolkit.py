import serial
import time
import argparse
import json
import socket
import random
import os
import sys
from request import Request
from gadgetlib import GadgetIdentifier, str_to_gadget_ident, GadgetMethod, str_to_gadget_method
from typing import Optional
from pprint import pprint

import client_control_methods
from network_connector import NetworkConnector
from serial_connector import SerialConnector
from mqtt_connector import MQTTConnector

NETWORK_MODES = ["serial", "mqtt"]
CONFIG_ATTRIBUTES = ["irrecv_pin", "irsend_pin", "radio_recv_pin", "radio_send_pin", "network_mode", "gadget_remote", "code_remote", "event_remote", "id", "wifi_ssid", "wifi_pw", "mqtt_ip", "mqtt_port", "mqtt_user", "mqtt_pw"]
PRIVATE_ATTRIBUTES = ["wifi_pw", "mqtt_pw"]
PUBLIC_ATTRIBUTES = [x for x in CONFIG_ATTRIBUTES if x not in PRIVATE_ATTRIBUTES]

parser = argparse.ArgumentParser(description='Script to upload configs to the controller')

# debug
parser.add_argument('--show_sending', action='store_true', help='prints the sent requests to the console')

# network mode
parser.add_argument("--network", help="may either be 'serial' or 'mqtt'")

# serial settings
parser.add_argument('--serial_port', help='serial port to connect to.')
parser.add_argument('--serial_baudrate', help='baudrate for the serial connection.')

# # mqtt settings
# parser.add_argument('--mqtt_port', help='port of the mqtt server.')
# parser.add_argument('--mqtt_ip', help='ip of the mqtt server.')

# config file
parser.add_argument('--config_file', help='path to the config that should be uploaded.')

# individual data
parser.add_argument('--wifi_id', help='id to be uploaded.')
parser.add_argument('--wifi_ssid', help='ssid to be uploaded.')
parser.add_argument('--wifi_pw', help='password to be uploaded.')
parser.add_argument('--mqtt_ip', help='mqtt ip to be uploaded.')
parser.add_argument('--mqtt_port', help='port to be uploaded.')
parser.add_argument('--mqtt_user', help='mqtt username to be uploaded.')
parser.add_argument('--mqtt_pw', help='mqtt password to be uploaded.')

parser.add_argument('--erase_eeprom',
                    action='store_true',
                    help='erases the eeprom and overwrites it')
parser.add_argument('--reset_eeprom',
                    action='store_true',
                    help='resets the complete config of the chip')
parser.add_argument('--reset_config',
                    action='store_true',
                    help='resets the system config but keeps the gadgets')
parser.add_argument('--reset_gadgets',
                    action='store_true',
                    help='resets the gadgets but keeps the system config')

parser.add_argument('--network_only',
                    action='store_true',
                    help='needs a config file. uploads only the network config.')
parser.add_argument('--id_only',
                    action='store_true',
                    help='needs a config file. uploads only the id.')
parser.add_argument('--monitor_mode',
                    action='store_true',
                    help='only uses the script as a read-only serial monitor')
parser.add_argument('--arg_attributes_only',
                    action='store_true',
                    help='so not load any config and just upload attributes set as script ')
ARGS = parser.parse_args()


def gen_req_id() -> int:
    """Generates a random Request ID"""

    return random.randint(0, 1000000)


def get_sender() -> str:
    """Returns the name used as sender (local hostname)"""

    return socket.gethostname()


def scan_for_clients() -> [str]:
    """Sends a broadcast and waits for clients to answer\
     Needs a global NetworkConnector named 'network_gadget'"""

    client_names = []
    req = Request("smarthome/broadcast/req",
                  gen_req_id(),
                  get_sender(),
                  None,
                  {})

    responses = network_gadget.send_broadcast(req)

    for broadcast_res in responses:
        client_names.append(broadcast_res.get_sender())

    return client_names


def config_args_existing() -> bool:
    """checks whether valid configs exist or not"""

    args_dict = vars(ARGS)
    for attr_name in CONFIG_ATTRIBUTES:
        if attr_name in args_dict and args_dict[attr_name] is not None:
            return True
    return False


def add_args_to_config(config: dict) -> dict:
    """Reads pre-set attributes from the ARGS into the config"""

    args_dict = vars(ARGS)
    for attr_name in CONFIG_ATTRIBUTES:
        if attr_name in args_dict and args_dict[attr_name] is not None:
            if config is None:
                config = {"name": "<args>", "description": "", "data": {}}
            config["data"][attr_name] = args_dict[attr_name]
    return config


def select_option(input_list: [str], category: str = None) -> int:
    """Presents every elem from the list and lets the user select one"""

    if category is None:
        print("Please select:")
    else:
        print("Please select a {}:".format(category))
    for i in range(len(input_list)):
        print("    {}: {}".format(i, input_list[i]))
    var = None
    while var is None:
        var = input("Please select an option by entering its number:\n")
        try:
            var = int(var)
        except TypeError:
            var = None
        if var < 0 or var >= len(input_list):
            print("Illegal input, try again.")
            var = None
    return var


def load_config_file(f_name: str) -> Optional[dict]:
    """Loads a config from the disk if possible"""

    try:
        with open(os.path.join("configs", f_name)) as json_file:
            cfg_json = json.load(json_file)
            if "name" not in cfg_json:
                cfg_json["name"] = f_name
            if "description" not in cfg_json:
                cfg_json["description"] = ""
            return cfg_json
    except IOError:
        return None


def select_config() -> Optional[dict]:
    """Scans for valid configs and lets the user select ont if needed and possible"""

    config_files = [f_name for f_name in os.listdir("configs") if
                    os.path.isfile(os.path.join("configs", f_name)) and f_name.endswith(".json")]
    valid_configs = []
    config_names = []
    for f_name in config_files:
        config_json = load_config_file(f_name)
        if json is not None:
            valid_configs.append(config_json)
            config_names.append(config_json["name"])

    if len(config_names) == 0:
        return None
    if len(config_names) == 1:
        return valid_configs[0]

    cfg_i = select_option(config_names, "config")
    return valid_configs[cfg_i]


def connect_to_client() -> Optional[str]:
    """Scans for clients and lets the user select one if needed and possible.\
     Needs a global NetworkConnector named 'network_gadget'"""

    client_id = None

    print("Please make sure your chip can receive serial requests")
    client_list = scan_for_clients()

    if len(client_list) == 0:
        print("No client answered to broadcast")
    elif len(client_list) > 1:
        client_id = select_option(client_list, "client to connect to")
    else:
        client_id = client_list[0]
        print("Connected to '{}'".format(client_id))
    return client_id


def load_config() -> Optional[dict]:
    """Loads a selected config and inserts possible ARGS parameters"""

    out_cfg = None
    if not ARGS.arg_attributes_only:
        if ARGS.config_file:
            out_cfg = load_config_file(ARGS.config_file)
        else:
            out_cfg = select_config()

    out_cfg = add_args_to_config(out_cfg)

    # Remove unknown attributes
    illegal_attributes = []
    for attr in out_cfg["data"]:
        if attr not in CONFIG_ATTRIBUTES:
            print("[!] Unknown attribute in config: '{}'".format(attr))
            illegal_attributes.append(attr)
    for attr in illegal_attributes:
        out_cfg["data"].pop(attr)

    # Translate the types for the gadgets from string to GadgetIdentifier
    if "gadgets" in out_cfg:
        for gadget_data in out_cfg["gadgets"]:

            # Check for name and type
            if "name" not in gadget_data or "type" not in gadget_data:
                print("[×] Illegal gadget config: missing 'name' or 'type'")
                return None
            if isinstance(gadget_data["type"], str):
                buf_type = str_to_gadget_ident(gadget_data["type"])
                if buf_type == GadgetIdentifier.err_type:
                    print("[×] Illegal gadget config: unknown type '{}'".format(type))
                    return None
                gadget_data["type"] = buf_type.value

            # Translate method names to indexes
            new_codes = {}
            if "codes" in gadget_data:
                for method in gadget_data["codes"]:
                    method_code = str_to_gadget_method(method).value
                    if method_code:
                        new_codes[method_code] = gadget_data["codes"][method]
                    else:
                        print("[!] Illegal gadget method: '{}'".format(method))

    return out_cfg


def read_client_config() -> dict:
    """Reads and returns all possible attributes from the client.\
     Needs a global NetworkConnector named 'network_gadget'"""

    out_settings = {}

    # for attr in [x for x in PUBLIC_ATTRIBUTES if x != "id"]:
    for attr in PUBLIC_ATTRIBUTES:

        payload_dict = {"param": attr}

        out_req = Request(path="smarthome/config/read",
                          session_id=gen_req_id(),
                          sender=get_sender(),
                          receiver=CLIENT_NAME,
                          payload=payload_dict)

        success, status, res = network_gadget.send_request(out_req)
        if res is not None and success is not False:
            # print("[✓] Reading '{}' was successful".format(attr))
            out_settings[attr] = res.get_payload()["value"]
        else:
            # print("[×] Reading '{}' failed".format(attr))
            out_settings[attr] = None
    return out_settings


def reset_config(client_name: str, reset_option: str) -> bool:
    """Resets the config of a client. Select behaviour using 'reset option'.\
     Needs a global NetworkConnector named 'network_gadget'"""

    return client_control_methods.reset_config(client_name,
                                               reset_option,
                                               get_sender(),
                                               network_gadget)


def reboot_client(client_name: str) -> bool:
    """Reboots the client to make changes take effect.\
     Needs a global NetworkConnector named 'network_gadget'"""

    return client_control_methods.reboot_client(client_name,
                                                get_sender(),
                                                network_gadget)


def upload_gadget(client_name: str, upl_gadget: dict) -> (bool, Optional[str]):
    """uploads a gadget to a client.\
     Needs a global NetworkConnector named 'network_gadget'"""

    return client_control_methods.upload_gadget(client_name,
                                                upl_gadget,
                                                get_sender(),
                                                network_gadget)


if __name__ == '__main__':

    network_gadget = None

    network_mode = None
    if ARGS.network:
        if ARGS.network == "serial":
            network_mode = 0
        elif ARGS.network == "mqtt":
            network_mode = 1
        else:
            print("Gave illegal network mode '{}'".format(ARGS.network))
            network_mode = select_option(NETWORK_MODES, "network mode")
    else:
        network_mode = select_option(NETWORK_MODES, "network mode")

    print()

    if network_mode == 0:  # SERIAL MODE
        if ARGS.serial_port:
            serial_port = ARGS.serial_port
        else:
            serial_port = '/dev/cu.SLAB_USBtoUART'

        if ARGS.serial_baudrate:
            serial_baudrate = ARGS.serial_baudrate
        else:
            serial_baudrate = 115200

        try:
            network_gadget = SerialConnector(get_sender(), serial_port, serial_baudrate)
        except (FileNotFoundError, serial.serialutil.SerialException) as e:
            print("Unable to connect to serial port '{}'".format(serial_port))
            sys.exit(1)

        if ARGS.monitor_mode:
            if network_gadget is not None:
                network_gadget.monitor()
                sys.exit(0)

    else:
        if ARGS.mqtt_port:
            mqtt_port = int(ARGS.mqtt_port)
        else:
            var = input("Please enter MQTT PORT:\n")
            try:
                mqtt_port = int(var)
            except ValueError:
                print("Illegal Port")
                sys.exit(1)

        if ARGS.mqtt_ip:
            mqtt_ip = ARGS.mqtt_ip
        else:
            mqtt_ip = input("Please enter MQTT IP:\n")

        try:
            network_gadget = MQTTConnector(get_sender(), mqtt_ip, mqtt_port)
        except (FileNotFoundError, serial.serialutil.SerialException) as e:
            print("Unable to connect to mqtt server '{}:{}'".format(mqtt_ip, mqtt_port))
            sys.exit(1)

    CLIENT_NAME = connect_to_client()

    if not CLIENT_NAME:
        print("Could not establish a connection to a client")
        sys.exit(1)

    print()

    if ARGS.erase_eeprom:
        if reset_config(CLIENT_NAME, "erase"):
            print("[✓] Erasing eeprom was successful")
        else:
            print("[×] Erasing eeprom failed")

    if ARGS.reset_eeprom:
        if reset_config(CLIENT_NAME, "complete"):
            print("[✓] Resetting the complete config was successful")
        else:
            print("[×] Resetting the complete config failed")

    if ARGS.reset_config:
        if reset_config(CLIENT_NAME, "config"):
            print("[✓] Resetting the system config was successful")
        else:
            print("[×] Resetting the system config failed")

    if ARGS.reset_gadgets:
        if reset_config(CLIENT_NAME, "gadgets"):
            print("[✓] Resetting the gadgets was successful")
        else:
            print("[×] Resetting the gadgets failed")

    CONFIG_FILE = load_config()
    print()

    if CONFIG_FILE is None:
        print("No config could be loaded")
        sys.exit(1)
    else:
        print("Config '{}' was loaded".format(CONFIG_FILE["name"]))
    print()

    for attr in CONFIG_ATTRIBUTES:
        if attr in CONFIG_FILE["data"]:
            attr_data = CONFIG_FILE["data"][attr]
            payload_dict = {"param": attr, "value": attr_data}

            out_req = Request(path="smarthome/config/write",
                              session_id=gen_req_id(),
                              sender=get_sender(),
                              receiver=CLIENT_NAME,
                              payload=payload_dict)

            success, status_msg, res = network_gadget.send_request(out_req)
            if success:
                print("[✓] Flashing '{}' was successful".format(attr))
                if attr == "id":
                    CLIENT_NAME = attr_data
            else:
                print("[×] Flashing '{}' failed".format(attr))

    print()

    if not ARGS.id_only and not ARGS.network_only:
        # upload gadgets
        if "gadgets" in CONFIG_FILE and CONFIG_FILE["gadgets"]:
            for gadget in CONFIG_FILE["gadgets"]:
                if "type" in gadget and "name" in gadget:
                    success, status = upload_gadget(CLIENT_NAME, gadget)
                    if success:
                        print("[✓] Uploading '{}' was successful".format(gadget["name"]))
                    else:
                        print("[×] Uploading '{}' failed: {}".format(gadget["name"], status))
                else:
                    print("[×] Cannot upload gadget without type or name")

        else:
            print("[i] No gadgets needed to be flashed")

    print()

    # reboot the client to apply all the changes
    if reboot_client(CLIENT_NAME):
        print("[✓] Rebooting client was successful")
    else:
        print("[×] Rebooting failed, please reboot manually if necessary")
