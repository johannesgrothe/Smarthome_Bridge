from abc import abstractmethod, ABCMeta

from lib.logging_interface import LoggingInterface


class ApiEncoderSuper(LoggingInterface, metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def encode(cls, obj) -> dict:
        """Encodes the object for the api"""
