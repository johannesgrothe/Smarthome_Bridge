"""Module to contain all sorts of client-write-functions to be shared between bridge and command line tool"""

import logging
from network.request import NoClientResponseException
from typing import Optional, Callable
from network.network_connector import NetworkConnector
from json_validator import Validator, ValidationError

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]

LOG_SENDER = "CONFIG_UPLOAD"
CONFIG_SCHEMA_NAME = "client_config"

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
    _validator: Validator
    _logger: logging.Logger

    def __init__(self, client_name: str, network_connector: NetworkConnector):
        self._client_name = client_name
        self._network = network_connector
        self._validator = Validator()
        self._logger = logging.getLogger("ClientController")

    def reset_config(self) -> bool:
        """Resets the config of a client. Select behaviour using 'reset option'."""

        payload = {}

        result = self._network.send_request("smarthome/config/reset", self._client_name, payload)
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
            self._validator.validate(config, CONFIG_SCHEMA_NAME)
        except ValidationError:
            self._logger.error("Config could not be written: Validation failed")
            raise ValidationError("Cannot validate json")

        payload_dict = {"config": config}

        result = self._network.send_request_split("smarthome/config/write", self._client_name, payload_dict, 50)

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
