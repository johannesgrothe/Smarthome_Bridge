from abc import ABC

from lib.logging_interface import LoggingInterface
from smarthome_bridge.api_encodable import ApiEncodable


class LocalGadget(LoggingInterface, ApiEncodable, ABC):
    _name: str

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name
