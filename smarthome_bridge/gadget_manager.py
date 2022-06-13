import threading
from typing import Optional

from lib.logging_interface import ILogging
from gadget_publishers.gadget_publisher import GadgetPublisher

from gadgets.remote.remote_gadget import RemoteGadget, Gadget
from gadgets.local.local_gadget import LocalGadget
from smarthome_bridge.gadget_status_supplier import GadgetStatusSupplier


class GadgetDoesntExistError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Gadget '{gadget_name}' does not exist")


class GadgetManager(ILogging, GadgetStatusSupplier):
    _gadgets: list[Gadget]
    _gadget_lock: threading.Lock

    _publishers: list[GadgetPublisher]
    _publisher_lock: threading.Lock

    def __init__(self):
        super().__init__()
        self._gadgets = []
        self._gadget_lock = threading.Lock()
        self._publishers = []
        self._publisher_lock = threading.Lock()

    def __del__(self):
        while self._gadgets:
            gadget = self._gadgets.pop()
            gadget.__del__()
        while self._publishers:
            publisher = self._publishers.pop()
            publisher.__del__()

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
            self._gadgets.append(gadget)
        with self._publisher_lock:
            for publisher in self._publishers:
                publisher.add_gadget(gadget.id)

    @property
    def gadgets(self) -> list[Gadget]:
        with self._gadget_lock:
            return self._gadgets

    @property
    def local_gadgets(self) -> list[LocalGadget]:
        with self._gadget_lock:
            return [x for x in self._gadgets if isinstance(x, LocalGadget)]

    @property
    def remote_gadgets(self) -> list[RemoteGadget]:
        with self._gadget_lock:
            return [x for x in self._gadgets if isinstance(x, RemoteGadget)]

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
