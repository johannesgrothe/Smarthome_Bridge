from threading import Thread
import logging
from chip_flasher import ChipFlasher, UploadFailedException, RepositoryAccessTimeout
from bridge import MainBridge

from network_connector import NetworkConnector
from typing import Optional
from mqtt_connector import MQTTConnector
from request import Request
import api
import socket_api
from client_controller import ClientController, NoClientResponseException


class BridgeMQTTThread(Thread):
    __parent_object: MainBridge
    __mqtt_connector: MQTTConnector

    def __init__(self, parent: MainBridge, connector: MQTTConnector):
        super().__init__()
        print("Creating Bridge MQTT Thread")
        self.__parent_object = parent
        self.__mqtt_connector = connector

    def run(self):
        print("Starting Bridge MQTT Thread")
        while True:
            buf_req: Optional[Request] = self.__mqtt_connector.get_request()
            if buf_req:
                self.__parent_object.handle_request(buf_req)


class BridgeAPIThread(Thread):
    __parent_object: MainBridge

    def __init__(self, parent: MainBridge):
        super().__init__()
        print("Creating Bridge API Thread")
        self.__parent_object = parent

    def run(self):
        print("Starting Bridge API Thread")
        buf_api_port = self.__parent_object.get_api_port()

        if buf_api_port == 0:
            print("API port not configured")
            return

        print("Launching API")
        api.run_api(self.__parent_object, buf_api_port)


class ChipConfigFlasherThread(Thread):
    __streaming_callback = None
    __config: dict
    __client_name: str
    __sender: str
    __network: NetworkConnector

    def __init__(self, sender: str, network: NetworkConnector, config: dict, client_name: str, callback=None):
        super().__init__()
        print("Chip Config Flasher Thread")
        self.__config = config
        self.__streaming_callback = callback
        self.__sender = sender
        self.__network = network
        self.__client_name = client_name

    def run(self):
        print("Starting config uploader thread")
        controller = ClientController(self.__client_name, self.__sender, self.__network)
        try:
            print("Starting config upload.")
            controller.write_config(self.__config, self.__streaming_callback)
            print("Config uploaded.")
        except NoClientResponseException:
            print("Config uploading failed..")


class ChipSWFlasherThread(Thread):
    _streaming_callback = None
    _branch: str
    _force_reset: bool
    _upload_port: Optional[str]
    _logger: logging.Logger

    def __init__(self, branch: str, force_reset: bool, serial_port: Optional[str] = None, callback=None):
        super().__init__()
        self._logger = logging.getLogger("ChipSWFlasherThread")
        self._logger.info("Creating ChipSWFlasherThread")
        self._branch = branch
        self._force_reset = force_reset
        self._upload_port = serial_port
        self._streaming_callback = callback

    def run(self):
        self._logger.info("Starting chip flasher thread")
        flasher = ChipFlasher(self._streaming_callback, max_delay=10)
        try:
            flasher.upload_software(self._branch, self._upload_port, self._force_reset)
            self._logger.info("Flashing done.")
        except UploadFailedException:
            self._logger.info("Flashing failed.")
        except RepositoryAccessTimeout:
            self._logger.info("Failed to access repository, maybe it is used by any other process.")
