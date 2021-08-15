from logging_interface import LoggingInterface
from abc import ABCMeta, abstractmethod
from typing import Callable

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector


class CharacteristicUpdateError(Exception):
    def __init__(self, gadget_name: str, characteristic: CharacteristicIdentifier):
        super().__init__(f"Failed to update characteristic '{characteristic}' on '{gadget_name}'")


class GadgetDeletionError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed to delete gadget '{gadget_name}'")


class GadgetCreationError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Failed create gadget '{gadget_name}' on external source")


class GadgetPublisher(LoggingInterface):

    _gadgets: list[Gadget]
    _update_connector: GadgetUpdateConnector

    def __init__(self, update_connector: GadgetUpdateConnector):
        super().__init__()
        self._gadgets = []
        self._update_connector = update_connector

    @abstractmethod
    def handle_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        """
        Updates a characteristic on a gadget.
        The gadget is passed to allow to check if anything has changed in the basic gadget structure.

        :param gadget: The gadget the changes are made on
        :param characteristic: The characteristic that has changed
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

        :param gadget: The gadget the changes took place on
        :param characteristic: The characteristic that was changed
        :return: None
        """
        self._logger.info(f"Publishing change at {characteristic} on {gadget.get_name()}")
        self._update_connector.forward_characteristic_update(gadget_name, characteristic, value)
