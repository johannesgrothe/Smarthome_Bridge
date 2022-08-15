from lib.logging_interface import ILogging
from abc import ABC
from typing import Optional

from smarthome_bridge.status_supplier_interfaces.gadget_status_receiver import GadgetStatusReceiver
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier


class GadgetUpdateError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to update gadget '{gadget_name}' on external source")


class GadgetDeletionError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to delete gadget '{gadget_name}' on external source")


class GadgetCreationError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed create gadget '{gadget_name}' on external source")


class GadgetPublisher(ILogging, GadgetStatusReceiver, ABC):

    _last_published_gadget: Optional[str]
    _status_supplier: Optional[GadgetStatusSupplier]

    def __init__(self):
        super().__init__()
        self._last_published_gadget = None
        self._status_supplier = None

    def __del__(self):
        self._logger.info(f"Deleting {self.__class__.__name__}")

    def set_status_supplier(self, supplier: GadgetStatusSupplier):
        self._status_supplier = supplier
