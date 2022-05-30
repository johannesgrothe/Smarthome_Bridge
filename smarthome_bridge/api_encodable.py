from abc import ABCMeta, abstractmethod


class ApiEncodable(metaclass=ABCMeta):

    @abstractmethod
    def encode_api(self) -> dict:
        """Encodes the component for the api"""
