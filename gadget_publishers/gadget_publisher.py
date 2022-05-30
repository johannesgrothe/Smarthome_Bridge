from lib.logging_interface import LoggingInterface
from abc import ABC
from typing import Optional
import threading

from smarthome_bridge.gadget_status_supplier import GadgetStatusSupplier, GadgetStatusReceiver


class GadgetUpdateError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to update gadget '{gadget_name}' on external source")


class GadgetDeletionError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to delete gadget '{gadget_name}' on external source")


class GadgetCreationError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed create gadget '{gadget_name}' on external source")


class GadgetPublisher(LoggingInterface, GadgetStatusReceiver, ABC):

    __publish_lock: threading.Lock
    _last_published_gadget: Optional[str]
    _status_supplier: Optional[GadgetStatusSupplier]

    def __init__(self):
        super().__init__()
        self.__publish_lock = threading.Lock()
        self._last_published_gadget = None
        self._status_supplier = None

    def __del__(self):
        self._logger.info(f"Deleting {self.__class__.__name__}")

    def set_status_supplier(self, supplier: GadgetStatusSupplier):
        self._status_supplier = supplier
