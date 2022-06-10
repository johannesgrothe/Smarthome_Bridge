"""Module for the homekit accessory wrapper"""
from abc import ABCMeta

from homekit.model import Accessory

from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants
from lib.logging_interface import ILogging
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher


class HomekitAccessoryWrapper(ILogging, metaclass=ABCMeta):
    """Superclass for all specific accessory wrappers"""
    _name: str
    _accessory: Accessory
    _publisher: GadgetPublisherHomekitInterface

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface):
        """
        Constructor for the accessory wrapper superclass

        :param name: Name of the accessory
        :param publisher: Publisher for this gadget
        """
        super().__init__()
        self._name = name
        self._publisher = publisher
        self._accessory = Accessory(self._name,
                                    HomekitConstants().manufacturer,
                                    self.__class__.__name__,
                                    HomekitConstants().serial_number,
                                    HomekitConstants().revision)
        # self._accessory.set_identify_callback(status_cb)

    @property
    def name(self) -> str:
        """Name of the homekit accessory"""
        return self._name

    @property
    def accessory(self) -> Accessory:
        """Actual library accessory"""
        return self._accessory
