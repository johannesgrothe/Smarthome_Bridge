import logging
from typing import Optional

from logging_interface import LoggingInterface
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier


class GadgetDoesntExistsError(Exception):
    def __init__(self, gadget_name: str):
        super().__init__(f"Gadget '{gadget_name}' does not exist")


class GadgetManager(LoggingInterface):

    _gadgets: list[Gadget]
    _gadget_publishers: list[GadgetPublisher]

    def __init__(self, publishers: list[GadgetPublisher]):
        super().__init__()
        self._gadgets = []
        self._gadget_publishers = publishers

    def __del__(self):
        pass

    def _get_gadget_by_name(self, name: str) -> Optional[Gadget]:
        for found_gadget in self._gadgets:
            if found_gadget.get_name() == name:
                return found_gadget
        return None

    def _update_gadget_on_publishers(self, gadget: Gadget):
        """
        Updates the gadget on all publishers

        :param gadget: The gadget with its new status to be processed by the publishers
        :return: None
        """
        for publisher in self._gadget_publishers:
            publisher.update_gadget(gadget)

    def _remove_gadget_from_publishers(self, gadget: Gadget):
        """
        Removes a gadget from all publishers

        :param gadget: The gadget that should be removed
        :return: None
        """
        for publisher in self._gadget_publishers:
            publisher.remove_gadget(gadget.get_name())

    def add_gadget(self, gadget: Gadget):
        found_gadget = self._get_gadget_by_name(gadget.get_name())
        if found_gadget is not None:
            self._remove_gadget(found_gadget)
        self._add_new_gadget(gadget)
        self._update_gadget_on_publishers(gadget)

    def remove_gadget(self, gadget_name: str):
        delete_gadget = self._get_gadget_by_name(gadget_name)
        if not delete_gadget:
            raise GadgetDoesntExistsError(gadget_name)
        self._remove_gadget(delete_gadget)

    def _add_new_gadget(self, gadget: Gadget):
        self._logger.info(f"Adding gadget '{gadget.get_name()}'")
        self._gadgets.append(gadget)

    def _remove_gadget(self, gadget: Gadget):
        self._logger.info(f"Removing gadget '{gadget.get_name()}'")
        self._gadgets.remove(gadget)
        self._remove_gadget_from_publishers(gadget)
        self._gadgets.remove(gadget)
