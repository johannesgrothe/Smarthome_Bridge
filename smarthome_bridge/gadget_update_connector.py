from typing import Optional, Callable
from logging_interface import LoggingInterface
from gadgets.gadget import CharacteristicIdentifier

CharacteristicUpdateCallback = Callable[[str, CharacteristicIdentifier, int], None]


class GadgetUpdateConnector(LoggingInterface):

    _characteristic_callback: Optional[CharacteristicUpdateCallback]

    def __init__(self, characteristic_callback: Optional[CharacteristicUpdateCallback]):
        super().__init__()
        self._characteristic_callback = characteristic_callback

    def forward_characteristic_update(self, gadget: str, characteristic: CharacteristicIdentifier, true_value: int):
        if self._characteristic_callback:
            self._characteristic_callback(gadget, characteristic, true_value)
