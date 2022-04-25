from abc import ABCMeta

from homekit.model import Accessory


from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants
from lib.logging_interface import LoggingInterface
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher


class HomekitAccessoryWrapper(LoggingInterface, GadgetUpdatePublisher, metaclass=ABCMeta):
    _name: str
    _accessory: Accessory
    _publisher: GadgetPublisherHomekitInterface

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface):
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
        return self._name

    @property
    def accessory(self) -> Accessory:
        return self._accessory
