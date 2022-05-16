import logging
import json
from time import sleep

from typing import Optional
from network.network_connector import NetworkConnector
from network.request import Request
from lib.pubsub import Publisher, Subscriber
from network.network_receiver import NetworkReceiver


class InconsistentHostnameException(Exception):
    def __init__(self, current: str, new: str):
        super().__init__(f"Difference in hostname between '{current}' (self) and '{new}' (other)")


class NoConnectorsException(Exception):
    def __init__(self):
        super().__init__(f"Cannot send a request without any connector present")


class NetworkManager(Publisher, Subscriber):
    _connectors: list[NetworkConnector]
    _hostname: Optional[str]
    _logger: logging.Logger
    _default_timeout: int

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connectors = []
        self._hostname = None
        self._default_timeout = 6

    def __del__(self):
        """
        Deletes the manager and all attached network connectors

        :return: None
        """
        while self._connectors:
            client = self._connectors.pop()
            client.__del__()

    def add_connector(self, connector: NetworkConnector):
        if connector not in self._connectors:
            if self._hostname is None:
                self._hostname = connector.get_hostname()
            else:
                if self._hostname != connector.get_hostname():
                    raise InconsistentHostnameException(self._hostname, connector.get_hostname())
            self._connectors.append(connector)
            connector.subscribe(self)

    def remove_connector(self, connector: NetworkConnector):
        if connector in self._connectors:
            self._connectors.remove(connector)

    def get_connector_count(self) -> int:
        return len(self._connectors)

    def receive(self, req: Request):
        self._logger.debug(f"Forwarding request from '{req.get_sender()}' at '{req.get_path()}'")
        self._publish(req)

    @staticmethod
    def _remove_doubles(xs: list) -> list:
        return list(dict.fromkeys(xs))

    def _create_request(self, path: str, receiver: Optional[str], payload: dict) -> Request:
        """
        Creates a request out of the given data

        :param path: Path for the request
        :param receiver: Receive of the request (None for broadcasts)
        :param payload: Payload of the request
        :return: The created request object
        :raises NoConnectorsException: If there is no connector added to get the hostname from
        """
        if not self._connectors:
            raise NoConnectorsException()
        self._logger.debug(f"Sending Request at '{path}'")
        out_req = Request(path,
                          None,
                          self._hostname,
                          receiver,
                          payload,
                          is_response=False)
        return out_req

    def _send_request_obj(self, req: Request, timeout: int, max_responses: int):
        req_receiver = NetworkReceiver()
        req_receiver.start_listening_for_responses()

        for connector in self._connectors:
            connector.subscribe(req_receiver)
            connector.send_request(req)

        responses = req_receiver.wait_for_responses(req, timeout, max_responses)
        return responses

    def set_default_timeout(self, timeout: Optional[int]):
        """
        Sets the default timeout used for requests

        :param timeout: Timeout value to use for requests without explicit timeout setting
        :return: None
        :raise ValueError: For timeout values below zero
        """
        # TODO: Tests fail if set to 1, investigate
        if timeout < 0:
            raise ValueError(timeout)
        self._logger.info(f"Changing default timeout from {self._default_timeout} to {timeout}")
        self._default_timeout = timeout

    def send_request(self, path: str, receiver: str, payload: dict, timeout: Optional[int] = None) -> Optional[Request]:
        """
        Sends a request and waits for a response by default.
        Returns the Response (if there is any).

        :param path: Path to send the request on
        :param receiver: Receiver of the request. Only responses by this Receiver will be permitted.
        :param payload: Payload of the sent request
        :param timeout: Ho long should be waited for any response to arrive
        :return: The Response (if there is any)
        """
        if timeout is None:
            timeout = self._default_timeout
        try:
            req = self._create_request(path, receiver, payload)
        except NoConnectorsException as err:
            self._logger.error(err.args[0])
            return None

        responses = self._send_request_obj(req, timeout, 1)
        if not responses:
            return None
        return responses[0]

    def send_broadcast(self, path: str, payload: dict, timeout: Optional[int] = None,
                       max_responses: Optional[int] = None) -> list[Request]:
        if timeout is None:
            timeout = self._default_timeout
        try:
            req = self._create_request(path, None, payload)
        except NoConnectorsException as err:
            self._logger.error(err.args[0])
            return []

        responses = self._send_request_obj(req, timeout, max_responses)
        return responses
