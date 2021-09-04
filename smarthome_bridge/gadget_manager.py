from typing import Optional

from logging_interface import LoggingInterface
from gadget_publishers.gadget_publisher import GadgetPublisher

from gadgets.gadget import Gadget
from gadgets.any_gadget import AnyGadget
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher, GadgetUpdateSubscriber
from gadgets.gadget_factory import GadgetFactory, GadgetCreationError


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

    def get_gadget(self, name: str) -> Optional[Gadget]:
        for found_gadget in self._gadgets:
            if found_gadget.get_name() == name:
                return found_gadget
        return None

    def get_gadget_ids(self) -> list[str]:
        return [x.get_name() for x in self._gadgets]

    def get_gadget_count(self) -> int:
        return len(self._gadgets)

    def receive_update(self, gadget: Gadget):
        found_gadget = self.get_gadget(gadget.get_name())
        if found_gadget is None:
            if not isinstance(gadget, AnyGadget):
                self._logger.info(f"Adding gadget '{gadget.get_name()}'")
                self._gadgets.append(gadget)
                self._publish_update(gadget)
            else:
                self._logger.error(f"Received sync data for unknown gadget '{gadget.get_name()}'")
        else:
            if gadget.__class__ == found_gadget.__class__ and gadget.equals_in_characteristic_values(found_gadget):
                return
            self._logger.info(f"Syncing existing gadget '{gadget.get_name()}'")
            self._gadgets.remove(found_gadget)
            try:
                factory = GadgetFactory()
                merged_gadget = factory.merge_gadgets(found_gadget, gadget)
            except GadgetCreationError as err:
                self._logger.error(err.args[0])
                return
            except NotImplementedError:
                self._logger.error(f"Merging gadgets of the type '{gadget.__class__.__name__}' is not implemented")
                return
            self._gadgets.append(merged_gadget)
            self._publish_update(merged_gadget)

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
        delete_gadget = self.get_gadget(gadget_name)
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
