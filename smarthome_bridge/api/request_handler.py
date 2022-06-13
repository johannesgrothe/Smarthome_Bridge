from abc import abstractmethod, ABCMeta

from lib.logging_interface import ILogging
from lib.validator_interface import IValidator
from network.request import Request
from smarthome_bridge.network_manager import NetworkManager


class RequestHandler(ILogging, IValidator, metaclass=ABCMeta):

    _network: NetworkManager

    def __init__(self, network: NetworkManager):
        super().__init__()
        self._network = network

    @abstractmethod
    def handle_request(self, req: Request) -> None:
        """
        Handles a request and responds to it

        :param req: Request to handle
        :return: None
        """
