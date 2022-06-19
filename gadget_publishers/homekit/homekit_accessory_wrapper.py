"""Module for the homekit accessory wrapper"""
from abc import ABCMeta

from homekit.model import Accessory

from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants
from gadgets.gadget import Gadget
from lib.logging_interface import ILogging


class HomekitAccessoryWrapper(ILogging, metaclass=ABCMeta):
    """Superclass for all specific accessory wrappers"""
    _accessory: Accessory
    _origin: Gadget

    def __init__(self, origin: Gadget):
        """
        Constructor for the accessory wrapper superclass

        :param origin: Gadget represented by this wrapper class
        """
        super().__init__()
        self._origin = origin
        self._logger.info(f"Creating new gadget with id '{self._origin.name}'")
        self._accessory = Accessory(self._origin.name,
                                    HomekitConstants().manufacturer,
                                    self.__class__.__name__,
                                    HomekitConstants().serial_number,
                                    HomekitConstants().revision)
        # self._accessory.set_identify_callback(status_cb)

    @property
    def name(self) -> str:
        """Name of the homekit accessory"""
        return self._origin.name

    @property
    def accessory(self) -> Accessory:
        """Actual library accessory"""
        return self._accessory
