"""Module for the homekit gadget publisher interface"""
from abc import abstractmethod, ABCMeta


class GadgetPublisherHomekitInterface(metaclass=ABCMeta):
    """Interface for the gadget update forwarding"""

    @abstractmethod
    def receive_update(self, gadget_name: str, update_data: dict) -> None:
        """
        Receive an update for the named gadget

        :param gadget_name: Name of the updated gadget
        :param update_data: Information about the updatd characteristics
        :return: None
        """
