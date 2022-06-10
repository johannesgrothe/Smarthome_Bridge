from abc import abstractmethod, ABCMeta

from lib.logging_interface import LoggingInterface
from network.request import Request


class RequestHandler(metaclass=ABCMeta, LoggingInterface):

    def __init__(self):


    @abstractmethod
    def handle_request(self, req: Request) -> None:
        """
        Handles a request and responds to it

        :param req: Request to handle
        :return: None
        """
