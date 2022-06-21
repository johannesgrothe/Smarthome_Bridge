import logging
import os.path
import threading
import time
from typing import Optional

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from gadget_publishers.gadget_publisher import GadgetPublisher, GadgetCreationError, GadgetDeletionError
from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants
from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_config_manager import HomekitConfigManager
from gadget_publishers.homekit.homekit_publisher_encoder import HomekitEncodeError, HomekitPublisherFactory
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.remote.remote_gadget import Gadget

RESTART_DELAY = 7
HOMEKIT_SERVER_NAME = "HomekitAccessoryServer"


class GadgetDoesNotExistError(Exception):
    pass


class GadgetPublisherHomekit(GadgetPublisher):
    _config_file: str
    _server_logger: logging.Logger
    _homekit_server: AccessoryServer
    _server_thread: Optional[threading.Thread]
    _gadgets: list[HomekitAccessoryWrapper]
    _restart_scheduled: bool

    def __init__(self, config: str):
        super().__init__()
        self._logger.info("Starting...")
        self._config_file = config
        if not os.path.isfile(self._config_file):
            HomekitConfigManager(self._config_file).generate_new_config()

        self._gadgets = []
        self._server_logger = logging.getLogger(HOMEKIT_SERVER_NAME)
        self._server_thread = None
        self._restart_scheduled = False
        self._dummy_accessory = Accessory("PythonBridge",
                                          HomekitConstants().manufacturer,
                                          self.__class__.__name__,
                                          "1776",
                                          HomekitConstants().revision)

        self.start_server()

    def __del__(self):
        super().__del__()
        self._restart_scheduled = False
        self.stop_server()
        while self._gadgets:
            gadget = self._gadgets.pop()
            gadget.__del__()

    @property
    def config(self) -> HomekitConfigManager:
        return HomekitConfigManager(self._config_file)

    def stop_server(self):
        if self._server_thread is None:
            self._logger.info("Accessory Server is not running")
            return
        self._logger.info("Stopping Accessory Server")
        self._homekit_server.unpublish_device()
        self._homekit_server.shutdown()
        self._server_thread.join()
        self._server_thread = None

    def start_server(self):
        if self._server_thread is not None:
            self.stop_server()
        self._logger.info("Starting Accessory Server")
        self._homekit_server = AccessoryServer(self._config_file, self._server_logger)

        self._homekit_server.add_accessory(self._dummy_accessory)

        for gadget in self._gadgets:
            self._homekit_server.add_accessory(gadget.accessory)
        self._homekit_server.publish_device()
        self._server_thread = threading.Thread(target=self._homekit_server.serve_forever,
                                               args=[1],
                                               name=HOMEKIT_SERVER_NAME,
                                               daemon=True)
        self._server_thread.start()

    def _schedule_restart(self):

        def restart_method(seconds: int):
            self._logger.info(f"Restarting in {seconds}s")
            time.sleep(seconds)
            self.start_server()

        if self._restart_scheduled:
            return

        restart_thread = threading.Thread(target=restart_method,
                                          args=[RESTART_DELAY],
                                          name=f"{self.__class__.__name__}RestartThread",
                                          daemon=True)
        self._restart_scheduled = True
        restart_thread.start()

    def _gadget_exists(self, name: str):
        return name in [x.name for x in self._gadgets]

    def _get_gadget(self, gadget_name: str) -> HomekitAccessoryWrapper:
        found = [x for x in self._gadgets if x.name == gadget_name]
        if not found:
            raise GadgetDoesNotExistError("Gadget does not exist")
        if len(found) != 1:
            raise Exception(f"More than one gadget with name {gadget_name} exists")
        return found[0]

    def create_gadget(self, gadget: Gadget):
        if self._gadget_exists(gadget.id):
            raise GadgetCreationError(gadget.id)
        try:
            gadget = HomekitPublisherFactory.encode(gadget)
            self._homekit_server.add_accessory(gadget.accessory)
            self._gadgets.append(gadget)
            self._homekit_server.publish_device()
            self._schedule_restart()
        except HomekitEncodeError:
            self._logger.info(f"Cannot create accessory for '{gadget.__class__.__name__}'")
            return

    def add_gadget(self, gadget_id: str):
        try:
            self.remove_gadget(gadget_id)
        except GadgetDeletionError:
            pass
        origin = self._status_supplier.get_gadget(gadget_id)
        self.create_gadget(origin)

    def remove_gadget(self, gadget_id: str):
        try:
            found = self._get_gadget(gadget_id)
            self._gadgets.remove(found)
            self._schedule_restart()
        except GadgetDoesNotExistError:
            raise GadgetDeletionError(gadget_id)

    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        pass  # not needed, accessory wrappers fetch data from origin gadget
