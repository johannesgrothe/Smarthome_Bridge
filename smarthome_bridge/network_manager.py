import logging
from typing import Optional
from network.network_connector import NetworkConnector
from network.request import Request
from pubsub import Publisher, Subscriber


class NetworkManager(Publisher, Subscriber):

    _connectors: list[NetworkConnector]
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connectors = []

    def __del__(self):
        while self._connectors:
            client = self._connectors.pop()
            client.__del__()

    def add_connector(self, connector: NetworkConnector):
        if connector not in self._connectors:
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

    # def send_request(self, path: str, receiver: str, payload: dict, timeout: int = 6) -> Optional[Request]:
    #     """
    #     Sends a request and waits for a response by default.
    #     Returns the Response (if there is any).
    #     """
    #     req = Request(path, None, self._hostname, receiver, payload)
    #     return self.__send_request_obj(req, timeout)
    #
    # def send_broadcast(self, path: str, payload: dict, timeout: int = 5,
    #                    max_responses: Optional[int] = None) -> list[Request]:
    #     req = Request(path, None, self._hostname, None, payload)
    #     self._send_data(req)
    #     req_receiver = NetworkReceiver(self)
    #     responses = req_receiver.wait_for_responses(req, timeout, max_responses)
    #     return responses
    #
    # def send_request_split(self, path: str, receiver: str, payload: dict, part_max_size: int = 30,
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

    def send_request(self, path: str, receiver: Optional[str], payload: dict, timeout: int = 6) -> Optional[Request]:
        self._logger.info(f"Sending Request at '{path}'")
        responses = []
        for network in self._connectors:
            if receiver is None:
                res = network.send_broadcast(path, payload, timeout)
            else:
                res = network.send_request(path, receiver, payload, timeout)
            if res:
                responses.append(res)
        responses = self._remove_doubles(responses)
        if len(responses) == 1:
            return responses[0]
        return None
