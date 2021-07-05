"""Module to contain all sorts of client-write-functions to be shared between bridge and command line tool"""

from jsonschema import validate, ValidationError
import json
import logging
from network.request import Request, NoClientResponseException
from typing import Optional, Callable
from network.network_connector import NetworkConnector

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]

LOG_SENDER = "CONFIG_UPLOAD"

_general_exit_code = 0

_upload_data_ok_code = 1
_upload_data_fail_code = -1

_upload_gadget_ok_code = 2
_upload_gadget_fail_code = -2
_upload_gadget_format_error_code = -3
_upload_gadget_no_gadget_in_cfg_code = 3


class ClientController:

    _client_name: str
    _sender_id: str
    _network: NetworkConnector
    _logger: logging.Logger

    def __init__(self, client_name: str, sender: str, network_connector: NetworkConnector):
        self._client_name = client_name
        self._sender_id = sender
        self._network = network_connector
        self._logger = logging.getLogger("ClientController")

    def reset_config(self) -> bool:
        """Resets the config of a client. Select behaviour using 'reset option'."""

        payload = {}

        out_request = Request(path="smarthome/config/reset",
                              session_id=None,
                              sender=self._sender_id,
                              receiver=self._client_name,
                              payload=payload)

        result = self._network.send_request(out_request)
        if not result:
            raise NoClientResponseException
        else:
            return result.get_ack()

    def reboot_client(self) -> bool:
        """Reboots the client to make changes take effect.\
         Needs a global NetworkConnector named 'network_gadget'"""

        payload = {"subject": "reboot"}

        result = self._network.send_request("smarthome/sys", self._client_name, payload)
        if not result:
            raise NoClientResponseException
        else:
            return result.get_ack()

    def write_config(self, config: dict, print_callback: CallbackFunction = None) -> bool:

        try:
            with open("json_schemas/client_config.json") as schema_file:
                schema = json.load(schema_file)
                validate(config, schema)
        except IOError:
            self._logger.error("Config could not be written: Schema could not be loaded")
            return False
        except ValidationError:
            self._logger.error("Config could not be written: Validation failed")
            return False

        payload_dict = {"config": config}

        out_req = Request(path="smarthome/config/write",
                          session_id=None,
                          sender=self._sender_id,
                          receiver=self._client_name,
                          payload=payload_dict)

        result = self._network.send_request_split(out_req, 50)

        if not result:
            if print_callback:
                print_callback(LOG_SENDER, _upload_data_fail_code, f"Received no response from client")
            raise NoClientResponseException
        else:
            if result.get_ack():
                if print_callback:
                    print_callback(LOG_SENDER, _upload_data_ok_code, f"Flashing config was successful")
                self._logger.info("Writing config was successful")
                return True
            else:
                if print_callback:
                    print_callback(LOG_SENDER, _upload_data_fail_code, f"Failed to write config")
                self._logger.error("Writing config failed")
                return False
