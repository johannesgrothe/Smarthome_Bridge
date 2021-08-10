from typing import Optional, Callable
from logging_interface import LoggingInterface
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier, Characteristic, CharacteristicIdentifier

CharacteristicUpdateCallback = Callable[[Gadget, CharacteristicIdentifier], None]


class GadgetUpdateConnector(LoggingInterface):

    _characteristic_callback: Optional[CharacteristicUpdateCallback]

    def __init__(self, characteristic_callback: Optional[CharacteristicUpdateCallback]):
        super().__init__()
        self._characteristic_callback = characteristic_callback

    def forward_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        if self._characteristic_callback:
            self._characteristic_callback(gadget, characteristic)
