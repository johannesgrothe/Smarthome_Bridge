from typing import Optional
from abc import abstractmethod

from network.request import Request
from pubsub import Publisher, Subscriber
from json_validator import Validator
from network.network_receiver import NetworkReceiver
from logging_interface import LoggingInterface

REQ_VALIDATION_SCHEME_NAME = "request_basic_structure"


class NetworkConnector(Publisher, Subscriber, LoggingInterface):
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
    def _send_data(self, req: Request):
        pass

    def send_request(self, req: Request, timeout: int = 6) -> Optional[Request]:
        self._logger.debug(f"Sending Request to '{req.get_path()}'")
        self._send_data(req)
        if timeout > 0:
            self._logger.debug(f"Waiting for Response ({timeout})...")
            req_receiver = NetworkReceiver(self)
            responses = req_receiver.wait_for_responses(req, timeout)
            if not responses:
                return None
            return responses[0]
        return None

    def receive(self, req: Request):
        self._publish(req)

    def get_hostname(self) -> str:
        return self._hostname
