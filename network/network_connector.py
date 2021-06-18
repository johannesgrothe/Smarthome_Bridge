import json
import logging
from typing import Optional
from time import sleep
from abc import abstractmethod

from network.request import Request, response_callback_type
from pubsub import Publisher, Subscriber
from json_validator import Validator
from network.network_receiver import NetworkReceiver

req_validation_scheme_name = "request_basic_structure"


class NetworkConnector(Publisher, Subscriber):
    """Class to implement an network interface prototype"""

    _logger: logging.Logger
    _validator: Validator
    _hostname: str

    def __init__(self, hostname: str):
        super().__init__()
        self._hostname = hostname
        self._logger = logging.getLogger(self.__class__.__name__)
        self._validator = Validator()

    def _validate_request(self, data: dict):
        self._validator.validate(data, req_validation_scheme_name)

    @abstractmethod
    def _send_data(self, req: Request):
        pass

    def __send_request_obj(self, req: Request, timeout: int = 6) -> Optional[Request]:
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

    def send_request(self, path: str, receiver: str, payload: dict, timeout: int = 6) -> Optional[Request]:
        """
        Sends a request and waits for a response by default.
        Returns the Response (if there is any).
        """
        req = Request(path, None, self._hostname, receiver, payload)
        return self.__send_request_obj(req, timeout)

    def send_broadcast(self, path: str, payload: dict, timeout: int = 5,
                       max_responses: Optional[int] = None) -> list[Request]:
        req = Request(path, None, self._hostname, None, payload)
        self._send_data(req)
        req_receiver = NetworkReceiver(self)
        responses = req_receiver.wait_for_responses(req, timeout, max_responses)
        return responses

    def send_request_split(self, path: str, receiver: str, payload: dict, part_max_size: int = 30,
                           timeout: int = 6) -> Optional[Request]:
        req = Request(path, None, self._hostname, receiver, payload)
        session_id = req.get_session_id()
        path = req.get_path()
        sender = req.get_sender()
        receiver = req.get_receiver()

        payload_str = json.dumps(req.get_payload())

        # Make string ready to be contained in json itself
        payload_str = payload_str.replace('"', "$*$")

        payload_len = len(payload_str)
        parts = []
        start = 0
        package_index = 0

        while start < payload_len:
            end = start + part_max_size
            payload_part = payload_str[start:(end if end < payload_len else payload_len)]
            parts.append(payload_part)
            start = end

        last_index = len(parts)

        for payload_part in parts:

            out_dict = {"package_index": package_index, "split_payload": payload_part}
            if package_index == 0:
                out_dict["last_index"] = last_index

            out_req = Request(path,
                              session_id,
                              sender,
                              receiver,
                              out_dict)
            if package_index == last_index - 1:
                res = self.__send_request_obj(out_req, timeout)

                return res
            else:
                self.__send_request_obj(out_req, 0)
            package_index += 1
            sleep(0.1)
        return None

    def get_hostname(self) -> str:
        return self._hostname

    def receive(self, req: Request):
        self._publish(req)
