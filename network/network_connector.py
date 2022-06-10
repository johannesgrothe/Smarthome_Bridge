from abc import abstractmethod

from network.request import Request
from lib.pubsub import Publisher, Subscriber
from utils.json_validator import Validator
from lib.logging_interface import ILogging

REQ_VALIDATION_SCHEME_NAME = "request_basic_structure"


class NetworkConnector(Publisher, Subscriber, ILogging):
    """Class to implement an network interface prototype"""

    _validator: Validator
    _hostname: str

    def __init__(self, hostname: str):
        super().__init__()
        self._validator = Validator()
        self._hostname = hostname

    def __del__(self):
        pass

    def _validate_request(self, data: dict):
        self._validator.validate(data, REQ_VALIDATION_SCHEME_NAME)

    @abstractmethod
    def _send_data(self, req: Request) -> None:
        pass

    def send_request(self, req: Request):
        self._logger.debug(f"Sending Request to '{req.get_path()}'")
        self._send_data(req)

    def receive(self, req: Request):
        self._publish(req)

    def get_hostname(self) -> str:
        return self._hostname
