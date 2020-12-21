"""Module to contain all sorts of client-write-functions to be shared between bridge and command line tool"""

import random
from request import Request
from typing import Optional
from network_connector import NetworkConnector


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

    suc, status_msg, result = network.send_request(out_request)
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

    suc, status_msg, result = network.send_request(out_request)
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

    suc, status_message, result = network.send_request(out_request)
    return suc is True, status_message

