import datetime
import json
import os
import threading
import time
from typing import Optional

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.local.i_local_gadget import ILocalGadget
from lib.logging_interface import ILogging
from gadget_publishers.gadget_publisher import GadgetPublisher
from smarthome_bridge.local_gadget_deserializer import LocalGadgetDeserializer
from smarthome_bridge.local_gadget_serializer import LocalGadgetSerializer

from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier
from utils.thread_manager import ThreadManager

DEFAULT_PUBLISH_DELAY: float = 0.5
DEFAULT_PUBLISH_TASK_INTERVAL: float = 0.1
DATA_FILE = "persistent_gadget_data.json"


class GadgetDoesntExistError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Gadget '{gadget_name}' does not exist")


class GadgetManager(ILogging, GadgetStatusSupplier, GadgetPublisherStatusSupplier):
    _publish_delay: float
    _task_interval: float

    _data_file: str

    _gadgets: list[Gadget]
    _gadget_lock: threading.Lock

    _publishers: list[GadgetPublisher]
    _publisher_lock: threading.Lock

    _threads: ThreadManager

    def __init__(self, data_directory: str, publish_delay: int = DEFAULT_PUBLISH_DELAY,
                 task_interval: int = DEFAULT_PUBLISH_TASK_INTERVAL):
        super().__init__()
        self._publish_delay = publish_delay
        self._task_interval = task_interval

        self._data_file = os.path.join(data_directory, DATA_FILE)

        self._gadgets = []
        self._gadget_lock = threading.Lock()

        self._publishers = []
        self._publisher_lock = threading.Lock()

        self._load_persistent_data()

        self._threads = ThreadManager()
        self._threads.add_thread(f"{self.__class__.__name__}UpdateApplier", self._update_applier_thread)
        self._threads.start_threads()

    def __del__(self):
        self._threads.__del__()
        with self._publisher_lock:
            while self._publishers:
                publisher = self._publishers.pop()
                publisher.__del__()
        with self._gadget_lock:
            while self._gadgets:
                gadget = self._gadgets.pop()
                gadget.__del__()

    def _load_persistent_data(self):
        self._logger.info("Loading data...")
        try:
            with open(self._data_file, "r") as file_p:
                data = json.load(file_p)
        except FileNotFoundError:
            return
        for gadget_data in data["gadgets"]:
            gadget = LocalGadgetDeserializer.deserialize(gadget_data)
            self.add_gadget(gadget)

    def save_persistent_data(self):
        self._logger.info("Saving data...")
        data = []
        for gadget in self.local_gadgets:
            data.append(LocalGadgetSerializer.serialize(gadget))
        save_data = {"gadgets": data}
        with open(self._data_file, "w") as file_p:
            json.dump(save_data, file_p)

    def _update_applier_thread(self):
        with self._gadget_lock:
            now = datetime.datetime.now()
            for gadget in self._gadgets:
                container = gadget.updated_properties
                if container.is_empty:
                    continue
                if (now - container.last_changed) > datetime.timedelta(seconds=self._publish_delay):
                    gadget.reset_updated_properties()
                    self._forward_update(container)
        time.sleep(self._task_interval)

    def _forward_update(self, container: GadgetUpdateContainer):
        with self._publisher_lock:
            for publisher in self._publishers:
                publisher.receive_gadget_update(container)

    def get_gadget(self, gadget_id: str) -> Optional[Gadget]:
        with self._gadget_lock:
            for found_gadget in self._gadgets:
                if found_gadget.id == gadget_id:
                    return found_gadget
        return None

    def add_gadget(self, gadget: Gadget):
        existing_gadget = self.get_gadget(gadget.id)
        with self._gadget_lock:
            if existing_gadget is not None:
                self._gadgets.remove(gadget)
                existing_gadget.__del__()
            self._gadgets.append(gadget)
        with self._publisher_lock:
            for publisher in self._publishers:
                publisher.add_gadget(gadget.id)
        if isinstance(gadget, ILocalGadget):
            self.save_persistent_data()

    def _get_gadgets(self) -> list[Gadget]:
        with self._gadget_lock:
            return self._gadgets

    def _get_publishers(self) -> list[GadgetPublisher]:
        with self._publisher_lock:
            return self._publishers

    def add_gadget_publisher(self, publisher: GadgetPublisher):
        """
        Adds a gadget publisher to the manager

        :param publisher: The publisher to add
        :return: None
        """
        self._logger.info(f"Adding gadget publisher '{publisher.__class__.__name__}'")
        with self._publisher_lock:
            if publisher not in self._publishers:
                publisher.set_status_supplier(self)
                self._publishers.append(publisher)
                with self._gadget_lock:
                    for gadget in self._gadgets:
                        publisher.add_gadget(gadget.id)
