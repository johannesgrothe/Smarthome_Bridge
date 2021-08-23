import logging
from typing import Optional
from network.network_connector import NetworkConnector
from network.request import Request
from pubsub import Publisher, Subscriber
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

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connectors = []
        self._hostname = None

    def __del__(self):
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

    def remove_connector(self, connector: NetworkConnector):
        if connector in self._connectors:
            self._connectors.remove(connector)

    def get_connector_count(self) -> int:
        return len(self._connectors)

    def receive(self, req: Request):
        self._forward_req(req)

    def _forward_req(self, req: Request):
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
        self._logger.info(f"Sending Request at '{path}'")
        out_req = Request(path,
                          None,
                          self._hostname,
                          receiver,
                          payload)
        return out_req

    def send_request(self, path: str, receiver: str, payload: dict, timeout: int = 6) -> Optional[Request]:
        """
        Sends a request and waits for a response by default.
        Returns the Response (if there is any).

        :param path: Path to send the request on
        :param receiver: Receiver of the request. Only responses by this Receiver will be permitted.
        :param payload: Payload of the sent request
        :param timeout: Ho long should be waited for any response to arrive
        :return: The Response (if there is any)
        """
        try:
            req = self._create_request(path, receiver, payload)
        except NoConnectorsException as err:
            self._logger.error(err.args[0])
            return None

        req_receiver = NetworkReceiver()
        req_receiver.start_listening_for_responses()

        for connector in self._connectors:
            connector.subscribe(req_receiver)
            connector.send_request(req)

        responses = req_receiver.wait_for_responses(req, timeout)
        if not responses:
            return None
        return responses[0]

    # def _send_broadcast(self, path: str, payload: dict, timeout: int = 5,
    #                    max_responses: Optional[int] = None) -> list[Request]:
    #     req = Request(path, None, self._hostname, None, payload)
    #     self._send_data(req)
    #     req_receiver = NetworkReceiver(self)
    #     responses = req_receiver.wait_for_responses(req, timeout, max_responses)
    #     return responses
    #
    # def _send_request_split(self, path: str, receiver: str, payload: dict, part_max_size: int = 30,
    #                        timeout: int = 6) -> Optional[Request]:
    #     req = Request(path, None, self._hostname, receiver, payload)
    #     session_id = req.get_session_id()
    #     path = req.get_path()
    #     sender = req.get_sender()
    #     receiver = req.get_receiver()
    #
    #     payload_str = json.dumps(req.get_payload())
    #
    #     # Make string ready to be contained in json itself
    #     payload_str = payload_str.replace('"', "$*$")
    #
    #     payload_len = len(payload_str)
    #     parts = []
    #     start = 0
    #     package_index = 0
    #
    #     while start < payload_len:
    #         end = start + part_max_size
    #         payload_part = payload_str[start:(end if end < payload_len else payload_len)]
    #         parts.append(payload_part)
    #         start = end
    #
    #     last_index = len(parts)
    #
    #     for payload_part in parts:
    #
    #         out_dict = {"package_index": package_index, "split_payload": payload_part}
    #         if package_index == 0:
    #             out_dict["last_index"] = last_index
    #
    #         out_req = Request(path,
    #                           session_id,
    #                           sender,
    #                           receiver,
    #                           out_dict)
    #         if package_index == last_index - 1:
    #             res = self.__send_request_obj(out_req, timeout)
    #
    #             return res
    #         else:
    #             self.__send_request_obj(out_req, 0)
    #         package_index += 1
    #         sleep(0.1)
    #     return None

    # def send_request(self, path: str, receiver: Optional[str], payload: dict, timeout: int = 6,
    #                  split: Optional[int] = None) -> Optional[Request]:
    #     if not self._connectors:
    #         self._logger.error("Cannot send request without anny connector")
    #         return None
    #     self._logger.info(f"Sending Request at '{path}'")
    #     out_req = Request(path,
    #                       None,
    #                       self._hostname,
    #                       receiver,
    #                       payload)
    #     if out_req.get_receiver() is None:
    #         max_responses = 50
    #     else:
    #         max_responses = 1
    #

        #
        # responses = []
        # for network in self._connectors:
        #     if receiver is None:
        #         res = network.send_broadcast(path, payload, timeout)
        #     else:
        #         res = network.send_request(path, receiver, payload, timeout)
        #     if res:
        #         responses.append(res)
        # responses = self._remove_doubles(responses)
        # if len(responses) == 1:
        #     return responses[0]
        # return None
