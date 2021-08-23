import logging
from typing import Optional

from logging_interface import LoggingInterface
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import CharacteristicIdentifier
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher, GadgetUpdateSubscriber


class GadgetDoesntExistError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Gadget '{gadget_name}' does not exist")


class GadgetManager(LoggingInterface, GadgetUpdatePublisher, GadgetUpdateSubscriber):

    _gadgets: list[Gadget]
    _gadget_publishers: list[GadgetPublisher]

    def __init__(self):
        super().__init__()
        self._gadgets = []
        self._gadget_publishers = []

    def __del__(self):
        while self._gadgets:
            gadget = self._gadgets.pop()
            gadget.__del__()
        while self._gadget_publishers:
            publisher = self._gadget_publishers.pop()
            publisher.__del__()

    def _get_gadget_by_name(self, name: str) -> Optional[Gadget]:
        for found_gadget in self._gadgets:
            if found_gadget.get_name() == name:
                return found_gadget
        return None

    @staticmethod
    def _gadgets_are_identical(first: Gadget, second: Gadget) -> bool:
        if first.__class__ != second.__class__:
            return False
        for characteristic in first.get_characteristic_types():
            first_c = first.get_characteristic(characteristic)
            second_c = second.get_characteristic(characteristic)
            if first_c != second_c:
                return False
            if first_c.get_step_value() != second_c.get_step_value():
                return False

        return first.get_name() == second.get_name()

    def receive_update(self, gadget: Gadget):
        found_gadget = self._get_gadget_by_name(gadget.get_name())
        if found_gadget is None:
            self._logger.info(f"Adding gadget '{gadget.get_name()}'")
            self._gadgets.append(gadget)
        else:
            if self._gadgets_are_identical(gadget, found_gadget):
                return
            self._logger.info(f"Syncing existing gadget '{gadget.get_name()}'")
            self._gadgets.remove(found_gadget)
            self._gadgets.append(gadget)
        self._publish_update(gadget)

    def _remove_gadget_from_publishers(self, gadget: Gadget):
        """
        Removes a gadget from all publishers

        :param gadget: The gadget that should be removed
        :return: None
        """
        self._logger.info(f"Removing gadget '{gadget.get_name()}' from {len(self._gadget_publishers)} publishers")
        for publisher in self._gadget_publishers:
            publisher.remove_gadget(gadget.get_name())

    def remove_gadget(self, gadget_name: str):
        """
        Removes a gadget from the manager and all its gadget publishers

        :param gadget_name: Name of the gadget to remove
        :return: None
        :raises GadgetDoesntExistError: If no gadget with the given name exists
        """
        delete_gadget = self._get_gadget_by_name(gadget_name)
        if not delete_gadget:
            raise GadgetDoesntExistError(gadget_name)
        self._gadgets.remove(delete_gadget)
        self._remove_gadget_from_publishers(delete_gadget)

    def add_gadget_publisher(self, publisher: GadgetPublisher):
        """
        Adds a gadget publisher to the manager

        :param publisher: The publisher to add
        :return: None
        """
        self._logger.info(f"Adding gadget publisher '{publisher.__class__.__name__}'")
        self.subscribe(publisher)
        publisher.subscribe(self)
        self._gadget_publishers.append(publisher)
        for gadget in self._gadgets:
            publisher.receive_update(gadget)
