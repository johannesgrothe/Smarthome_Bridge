import serial
import time
import argparse
import json
import re
import socket
import random
import os
import sys
from request import Request
from gadgetlib import GadgetIdentifier, str_to_gadget_ident
from typing import Union, Optional
from pprint import pprint

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
parser.add_argument('--port', help='serial port to connect to.')
parser.add_argument('--baudrate', help='baudrate for the serial connection.')

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


def decode_line(line) -> Optional[Request]:
    """Decodes a line and extracts a request if there is any"""

    if line[:3] == "!r_":
        elems = re.findall("_([a-z])\[(.+?)\]", line)
        req_dict = {}
        for type, val in elems:
            if type in req_dict:
                print("Double key in request: '{}'".format(type))
                return None
            else:
                req_dict[type] = val
        for key in ["p", "b"]:
            if key not in req_dict:
                print("Missig key in request: '{}'".format(key))
                return None
        try:
            json_body = json.loads(req_dict["b"])

            out_req = Request(path=req_dict["p"],
                              session_id=json_body["session_id"],
                              sender=json_body["sender"],
                              receiver=json_body["receiver"],
                              payload=json_body["payload"])

            return out_req
        except ValueError:
            return None
    return None


def send_serial(req: Request) -> bool:
    """Sends a request on the serial port"""

    req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(), str(req.get_body()).replace("'", '"').replace("None", "null"))
    if ARGS.show_sending:
        print("Sending '{}'".format(req_line[:-1]))
    ser.write(req_line.encode())
    return True


def read_serial(timeout: int = 0, monitor_mode: bool = False) -> Optional[Request]:
    """Tries to read a line from the serial port"""

    timeout_time = time.time() + timeout
    while True:
        try:
            ser_bytes = ser.readline().decode()
            # if ser_bytes.startswith("!"):
            # print("   -> {}".format(ser_bytes[:-1]))
            if monitor_mode:
                print(ser_bytes[:-1])
            else:
                if ser_bytes.startswith("Backtrace: 0x"):
                    print("Client crashed with {}".format(ser_bytes[:-1]))
                    return None
                buf_req = decode_line(ser_bytes)
                if buf_req:
                    return buf_req
        except (FileNotFoundError, serial.serialutil.SerialException):
            print("Lost connection to serial port")
            return None
        if (timeout > 0) and (time.time() > timeout_time):
            return None


def send_request(req: Request) -> (Optional[bool], Optional[Request]):
    """Sends a request on the serial port and waits for the answer"""

    send_serial(req)
    timeout_time = time.time() + 6
    while time.time() < timeout_time:
        remaining_time = timeout_time - time.time()
        res = read_serial(2 if remaining_time > 2 else remaining_time)
        if res and res.get_session_id() == req.get_session_id():
            res_ack = res.get_ack()
            res_status_msg = res.get_status_msg()
            return res_ack, res_status_msg, res
    return None, None


def scan_for_clients() -> [str]:
    """Sends a broadcast and waits for clients to answer"""

    client_names = []
    session_id = gen_req_id()
    req = Request("smarthome/broadcast/req",
                  session_id,
                  get_sender(),
                  None,
                  {})
    send_serial(req)
    timeout_time = time.time() + 6
    while time.time() < timeout_time:
        remaining_time = timeout_time - time.time()
        req = read_serial(2 if remaining_time > 2 else remaining_time)
        if req and req.get_path() == "smarthome/broadcast/res" and req.get_session_id() == session_id:
            if network_mode == 0:
                return [req.get_sender()]
            else:
                client_names.append(req.get_sender())
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
    """Scans for clients and lets the user select one if needed and possible"""

    client_id = None

    print("Please make sure your chip can receive serial requests")
    client_list = scan_for_clients()

    if len(client_list) == 0:
        print("No client answered to broadcast")
    elif len(client_list) > 1:
        print("Multiple clients answered to broadcast (wtf)")
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
            if "name" not in gadget_data or "type" not in gadget_data:
                print("[×] Illegal gadget config: missing 'name' or 'type'")
                return None
            if isinstance(gadget_data["type"], str):
                buf_type = str_to_gadget_ident(gadget_data["type"])
                if buf_type == GadgetIdentifier.err_type:
                    print("[×] Illegal gadget config: unknown type '{}'".format(type))
                    return None
                gadget_data["type"] = buf_type.value

    return out_cfg


def read_client_config() -> dict:
    """Reads and returns all possible attributes from the client"""

    out_settings = {}

    # for attr in [x for x in PUBLIC_ATTRIBUTES if x != "id"]:
    for attr in PUBLIC_ATTRIBUTES:

        payload_dict = {"param": attr}

        out_req = Request(path="smarthome/config/read",
                          session_id=gen_req_id(),
                          sender=get_sender(),
                          receiver=CLIENT_NAME,
                          payload=payload_dict)

        success, status, res = send_request(out_req)
        if res is not None and success is not False:
            # print("[✓] Reading '{}' was successful".format(attr))
            out_settings[attr] = res.get_payload()["value"]
        else:
            # print("[×] Reading '{}' failed".format(attr))
            out_settings[attr] = None
    return out_settings


def reset_config(client_name: str, reset_option: str) -> bool:
    """resets the config of a client. select behaviour using 'reset option'"""

    payload = {"reset_option": reset_option}

    out_request = Request(path="smarthome/config/reset",
                          session_id=gen_req_id(),
                          sender=get_sender(),
                          receiver=client_name,
                          payload=payload)

    suc, status_msg, result = send_request(out_request)
    return suc


def reboot_client(client_name: str) -> bool:
    """Reboots the client to make changes take effect"""

    payload = {"subject": "reboot"}

    out_request = Request(path="smarthome/sys",
                          session_id=gen_req_id(),
                          sender=get_sender(),
                          receiver=client_name,
                          payload=payload)

    suc, status_msg, result = send_request(out_request)
    return suc is True


def upload_gadget(client_name: str, gadget: dict) -> (bool, Optional[str]):
    """uploads a gadget to a client"""

    if "type" not in gadget or "name" not in gadget:
        return False

    out_request = Request(path="smarthome/gadget/add",
                          session_id=gen_req_id(),
                          sender=get_sender(),
                          receiver=client_name,
                          payload=gadget)

    suc, status_message, result = send_request(out_request)
    return suc is True, status_message


if __name__ == '__main__':

    network_mode = None
    if ARGS.network:
        if ARGS.network == "serial":
            network_mode = 0
        elif ARGS.network == "mqtt":
            network_mode = 1
        else:
            print("Gave illegal network mode '{}'".format(ARGS.network == "mqtt"))
            network_mode = select_option(NETWORK_MODES, "network mode")
    else:
        network_mode = select_option(NETWORK_MODES, "network mode")

    print()

    if network_mode == 0:  # SERIAL MODE
        if ARGS.port:
            serial_port = ARGS.port
        else:
            serial_port = '/dev/cu.SLAB_USBtoUART'

        if ARGS.baudrate:
            serial_baudrate = ARGS.baudrate
        else:
            serial_baudrate = 115200

        serial_active = False
        try:
            ser = serial.Serial(port=serial_port, baudrate=serial_baudrate, timeout=1)
            ser.flushInput()
            serial_active = True
        except (FileNotFoundError, serial.serialutil.SerialException) as e:
            print("Unable to connect to serial port '{}'".format(serial_port))

        if serial_active:
            if ARGS.monitor_mode:
                read_serial(0, True)
                sys.exit(0)
        else:
            sys.exit(1)

    else:
        print("MQTT is currently not supported")
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

            success, status_msg, res = send_request(out_req)
            if success:
                print("[✓] Flashing '{}' was successful".format(attr))
                if attr == "id":
                    CLIENT_NAME = attr_data
            else:
                print("[×] Flashing '{}' failed".format(attr))

    print()
    # CLIENT_SETTINGS = read_client_config()
    #
    # print("Client Config:")
    # for attr in CLIENT_SETTINGS:
    #     print("   '{}': '{}'".format(attr, CLIENT_SETTINGS[attr]))

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
