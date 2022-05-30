from abc import ABC

from lib.logging_interface import LoggingInterface


class LocalGadget(LoggingInterface, ABC):
    _id: str

    def __init__(self, name: str):
        super().__init__()
        self._id = name

    @property
    def id(self):
        return self._id
