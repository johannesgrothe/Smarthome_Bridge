from logging_interface import LoggingInterface
from abc import ABCMeta, abstractmethod
from typing import Callable

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector


class GadgetPublisher(LoggingInterface):

    _gadgets: list[Gadget]
    _update_connector: GadgetUpdateConnector

    def __init__(self, update_connector: GadgetUpdateConnector):
        super().__init__()
        self._gadgets = []
        self._update_connector = update_connector

    @abstractmethod
    def handle_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier) -> bool:
        """
        Updates a characteristic on a gadget.
        The gadget is passed to allow to check if anything has changed in the basic gadget structure.

        :param gadget: The gadget the changes are made on
        :param characteristic: The characteristic that has changed
        :return: None
        """
        pass

    @abstractmethod
    def remove_gadget(self, gadget_name: str) -> bool:
        """
        Removes a gadget from the publishing interface

        :param gadget_name: Name of the gadget to remove
        :return: None
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
