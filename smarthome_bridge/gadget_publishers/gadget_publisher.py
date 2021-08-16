from logging_interface import LoggingInterface
from abc import ABCMeta, abstractmethod
from typing import Callable, Optional

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector


class CharacteristicUpdateError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to update characteristic '{characteristic}' on '{gadget_name}'")


class GadgetDeletionError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to delete gadget '{gadget_name}'")


class GadgetCreationError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed create gadget '{gadget_name}' on external source")


class GadgetPublisher(LoggingInterface):

    _gadgets: list[Gadget]
    _update_connector: Optional[GadgetUpdateConnector]

    def __init__(self):
        super().__init__()
        self._gadgets = []
        self._update_connector = None

    def __del__(self):
        self._logger.info(f"Deleting {self.__class__.__name__}")

    def set_update_connector(self, connector: GadgetUpdateConnector):
        self._update_connector = connector

    @abstractmethod
    def handle_update(self, gadget: Gadget):
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
    def remove_gadget(self, gadget_name: str) -> bool:
        """
        Removes a gadget from the publishing interface

        :param gadget_name: Name of the gadget to remove
        :return: None
        :raises GadgetDeletionError: If any error occurred during deleting
        """
        pass

    def _publish_characteristic_update(self, gadget_name: str, characteristic: CharacteristicIdentifier, value: int):
        """
        Updates the parent object with new information

        :param gadget_name: The name of the changed gadget
        :param characteristic: The characteristic that was changed
        :param value: The new value of the characteristic
        :return: None
        """
        self._logger.info(f"Publishing change at {characteristic} on {gadget_name}")
        if self._update_connector:
            self._update_connector.forward_characteristic_update(gadget_name, characteristic, value)
        else:
            self._logger.error("Cannot forward characteristic update: No update connector registered")
