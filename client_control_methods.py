"""Module to contain all sorts of client-write-functions to be shared between bridge and command line tool"""

import random
from jsonschema import validate, ValidationError
import json
from request import Request
from typing import Optional, Callable
from network_connector import NetworkConnector

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]

CONFIG_ATTRIBUTES = ["irrecv_pin", "irsend_pin", "radio_recv_pin", "radio_send_pin", "network_mode",
                     "gadget_remote", "code_remote", "event_remote", "id", "wifi_ssid", "wifi_pw",
                     "mqtt_ip", "mqtt_port", "mqtt_user", "mqtt_pw"]
PRIVATE_ATTRIBUTES = ["wifi_pw", "mqtt_pw"]
PUBLIC_ATTRIBUTES = [x for x in CONFIG_ATTRIBUTES if x not in PRIVATE_ATTRIBUTES]
LOG_SENDER = "CONFIG_UPLOAD"

__general_exit_code = 0

__upload_data_ok_code = 1
__upload_data_fail_code = -1

__upload_gadget_ok_code = 2
__upload_gadget_fail_code = -2
__upload_gadget_format_error_code = -3
__upload_gadget_no_gadget_in_cfg_code = 3


def gen_req_id() -> int:
    """Generates a random Request ID"""

    return random.randint(0, 1000000)


def reset_config(client_name: str, reset_option: str, sender: str, network: NetworkConnector) -> bool:
    """Resets the config of a client. Select behaviour using 'reset option'."""

    payload = {"reset_option": reset_option}

    out_request = Request(path="smarthome/config/reset",
                          session_id=gen_req_id(),
                          sender=sender,
                          receiver=client_name,
                          payload=payload)

    suc, result = network.send_request(out_request)
    return suc


def reboot_client(client_name: str, sender: str, network: NetworkConnector) -> bool:
    """Reboots the client to make changes take effect.\
     Needs a global NetworkConnector named 'network_gadget'"""

    payload = {"subject": "reboot"}

    out_request = Request(path="smarthome/sys",
                          session_id=gen_req_id(),
                          sender=sender,
                          receiver=client_name,
                          payload=payload)

    suc, result = network.send_request(out_request)
    return suc is True


def upload_gadget(client_name: str, gadget: dict, sender: str, network: NetworkConnector) -> (bool, Optional[str]):
    """uploads a gadget to a client."""

    if "type" not in gadget or "name" not in gadget:
        return False

    out_request = Request(path="smarthome/gadget/add",
                          session_id=gen_req_id(),
                          sender=sender,
                          receiver=client_name,
                          payload=gadget)

    suc, result = network.send_request(out_request)
    return suc is True, result.get_status_msg()


def write_config(client_name: str, config: dict, sender: str, network: NetworkConnector,
                 print_callback: CallbackFunction = None):

    try:
        with open("json_schemas/client_config.json") as schema_file:
            schema = json.load(schema_file)
            validate(config, schema)
    except IOError:
        print("Config could not be written: Schema could not be loaded")
        return
    except ValidationError:
        print("Config could not be written: Validation failed")
        return

    payload_dict = {"type": "complete",
                    "reset_config": True,
                    "reset_gadgets": True,
                    "config": config}

    out_req = Request(path="smarthome/config/write",
                      session_id=gen_req_id(),
                      sender=sender,
                      receiver=client_name,
                      payload=payload_dict)

    success, res = network.send_request_split(out_req, 50)

    if success:
        if print_callback:
            print_callback(LOG_SENDER, __upload_data_ok_code, f"Flashing '{attr}' was successful")
        print("Writing config was successful")
    else:
        print("Writing config failed")
