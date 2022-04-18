from lib.logging_interface import LoggingInterface
from abc import ABCMeta, abstractmethod
from typing import Optional
import threading

from gadgets.gadget import Gadget
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher, GadgetUpdateSubscriber
from smarthome_bridge.gadget_status_supplier import GadgetStatusSupplier


class GadgetUpdateError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to update gadget '{gadget_name}' on external source")


class GadgetDeletionError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to delete gadget '{gadget_name}' on external source")


class GadgetCreationError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed create gadget '{gadget_name}' on external source")


class GadgetPublisher(LoggingInterface, GadgetUpdatePublisher, GadgetUpdateSubscriber, metaclass=ABCMeta):

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

    @abstractmethod
    def receive_gadget(self, gadget: Gadget):
        """
        Updates a gadget. It will be created if it does not exist yet and it will detect which characteristics have
        changed and update those in need of updating
        :param gadget: The gadget the changes are made on
        :return: None
        :raises CharacteristicUpdateError: If any error occurred during updating
        """
        pass

    @abstractmethod
    def create_gadget(self, gadget: Gadget):
        """
        Creates/Saves a new gadget

        :param gadget: Gadget to create
        :return: None
        :raises GadgetCreationError: If any error occurs during gadget creation
        """
        pass

    @abstractmethod
    def remove_gadget(self, gadget_name: str):
        """
        Removes a gadget from the publishing interface

        :param gadget_name: Name of the gadget to remove
        :return: None
        :raises GadgetDeletionError: If any error occurred during deleting
        """
        pass

    def _publish_gadget(self, gadget: Gadget):
        with self.__publish_lock:
            self._last_published_gadget = gadget.get_name()
            super()._publish_gadget(gadget)
            self._last_published_gadget = None
