"""Module to contain all sorts of client-write-functions to be shared between bridge and command line tool"""

import logging
import time

from logging_interface import LoggingInterface
from network.request import NoClientResponseException, Request
from typing import Optional, Callable

from pubsub import Subscriber
from smarthome_bridge.network_manager import NetworkManager
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


class ClientController(LoggingInterface):
    _client_name: str
    _network: NetworkManager
    _validator: Validator

    def __init__(self, client_name: str, network_connector: NetworkManager):
        super().__init__()
        self._client_name = client_name
        self._network = network_connector
        self._validator = Validator()

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

    def write_config(self, config: dict) -> bool:
        """Writes a config to the client"""

        try:
            self._validator.validate(config, CONFIG_SCHEMA_NAME)
        except ValidationError:
            self._logger.error("Config could not be written: Validation failed")
            raise ValidationError("Cannot validate json")

        payload_dict = {"config": config}

        result = self._network.send_request_split("smarthome/config/write", self._client_name, payload_dict, 50)

        if not result:
            raise NoClientResponseException
        else:
            return result.get_ack()
