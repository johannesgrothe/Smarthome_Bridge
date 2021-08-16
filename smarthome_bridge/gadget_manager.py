import logging
from typing import Optional

from logging_interface import LoggingInterface
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import CharacteristicIdentifier


class GadgetDoesntExistError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Gadget '{gadget_name}' does not exist")


class GadgetManager(LoggingInterface):

    _gadgets: list[Gadget]
    _gadget_publishers: list[GadgetPublisher]
    _update_connector: GadgetUpdateConnector

    def __init__(self):
        super().__init__()
        self._gadgets = []
        self._gadget_publishers = []
        self._update_connector = GadgetUpdateConnector(self._handle_characteristic_update)

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

    def _handle_characteristic_update(self, gadget_name: str, characteristic: CharacteristicIdentifier, value: int):
        pass

    def _update_gadget_on_publishers(self, gadget: Gadget):
        """
        Updates the gadget on all publishers

        :param gadget: The gadget with its new status to be processed by the publishers
        :return: None
        """
        self._logger.info(f"Syncing existing gadget '{gadget.get_name()}'"
                          f"with {len(self._gadget_publishers)} publishers")
        for publisher in self._gadget_publishers:
            publisher.handle_update(gadget)

    def _remove_gadget_from_publishers(self, gadget: Gadget):
        """
        Removes a gadget from all publishers

        :param gadget: The gadget that should be removed
        :return: None
        """
        self._logger.info(f"Removing gadget '{gadget.get_name()}' from {len(self._gadget_publishers)} publishers")
        for publisher in self._gadget_publishers:
            publisher.remove_gadget(gadget.get_name())

    def sync_gadget(self, gadget: Gadget):
        found_gadget = self._get_gadget_by_name(gadget.get_name())
        if found_gadget is None:
            self._logger.info(f"Adding gadget '{gadget.get_name()}'")
            self._gadgets.append(gadget)
        else:
            self._logger.info(f"Syncing existing gadget '{gadget.get_name()}'")
        self._update_gadget_on_publishers(gadget)

    def remove_gadget(self, gadget_name: str):
        delete_gadget = self._get_gadget_by_name(gadget_name)
        if not delete_gadget:
            raise GadgetDoesntExistError(gadget_name)
        self._gadgets.remove(delete_gadget)
        self._remove_gadget_from_publishers(delete_gadget)

    def add_gadget_publisher(self, publisher: GadgetPublisher):
        self._logger.info(f"Adding gadget publisher '{publisher.__class__.__name__}'")
        self._gadget_publishers.append(publisher)
        publisher.set_update_connector(self._update_connector)
        for gadget in self._gadgets:
            publisher.handle_update(gadget)
