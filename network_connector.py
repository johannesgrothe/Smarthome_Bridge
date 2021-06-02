import json
import logging
from typing import Optional
from queue import Queue
from datetime import datetime, timedelta
from time import sleep
from abc import abstractmethod

from request import Request
from pubsub import Publisher, Subscriber
from json_validator import Validator


_req_validation_scheme_name = "request_basic_structure"


class NetworkReceiver(Subscriber):

    _request_queue: Queue
    _keep_queue: bool

    def __init__(self, network: Publisher):
        super().__init__()
        self._request_queue = Queue()
        self._keep_queue = False
        self._network = network
        self._network.subscribe(self)

    def __del__(self):
        pass

    def receive(self, req: Request):
        self._request_queue.put(req)

    def start_listening_for_responses(self):
        """Clears the queue and starts recording requests.
        All received requests are used the next time wait_for_responses() is called."""
        self._request_queue = Queue()
        self._keep_queue = True

    def wait_for_responses(self, out_req: Request, timeout: int = 300, max_resp_count: Optional[int] = 1) -> list[Request]:
        if not self._keep_queue:
            self._request_queue = Queue()
        else:
            self._keep_queue = False

        responses: list[Request] = []
        timeout_time = datetime.now() + timedelta(seconds=timeout)

        while timeout and datetime.now() < timeout_time:
            if not self._request_queue.empty():
                res: Request = self._request_queue.get()
                if res.get_session_id() == out_req.get_session_id() and out_req.get_sender() != res.get_sender():

                    responses.append(res)

                    if max_resp_count and len(responses) >= max_resp_count:
                        return responses

        return responses


class NetworkConnector(Publisher):
    """Class to implement an network interface prototype"""

    _logger: logging.Logger
    _validator: Validator

    __part_data: dict
    _name: str

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._logger = logging.getLogger(self.__class__.__name__)
        self._validator = Validator()

        self.__part_data = {}

    def __del__(self):
        pass

    def _validate_request(self, data: dict):
        self._validator.validate(data, _req_validation_scheme_name)

    @abstractmethod
    def _send_data(self, req: Request):
        self._logger.error(f"Not implemented: '_send_data'")

    @abstractmethod
    def _receive_data(self) -> Optional[Request]:
        self._logger.error(f"Not implemented: '_receive_data'")
        return None

    def _receive(self):
        """Tries to receive a new request from the network and publishes it to its subscribers"""
        received_request = self._receive_data()
        if received_request:

            if received_request.get_receiver() is not None and received_request.get_receiver() != self._name:
                return  # Request is not for me

            req_payload = received_request.get_payload()
            if "package_index" in req_payload and "split_payload" in req_payload:
                id_str = str(received_request.get_session_id())
                p_index = req_payload["package_index"]
                split_payload = req_payload["split_payload"]
                if p_index == 0:
                    if "last_index" in req_payload:
                        l_index = req_payload["last_index"]
                        buf_json = {"start_req": received_request, "last_index": l_index, "payload_bits": []}
                        for i in range(l_index + 1):
                            buf_json["payload_bits"].append(None)
                        buf_json["payload_bits"][0] = split_payload
                        self.__part_data[id_str] = buf_json
                    else:
                        self._logger.error("Received first block of split request without last_index")
                else:
                    if id_str in self.__part_data:
                        req_data = self.__part_data[id_str]
                        req_data["payload_bits"][p_index] = split_payload
                        if p_index >= req_data["last_index"] - 1:
                            end_data = ""
                            for str_data in req_data["payload_bits"]:
                                if str_data is None:
                                    self._logger.error("Detected missing data block in split request")
                                    break
                                end_data += str_data
                            try:
                                end_data = end_data.replace("$*$", '"')
                                json_data = json.loads(end_data)
                                first_req: Request = req_data["start_req"]

                                out_req = Request(first_req.get_path(),
                                                  first_req.get_session_id(),
                                                  first_req.get_sender(),
                                                  first_req.get_receiver(),
                                                  json_data)
                                self._publish(out_req)
                                del self.__part_data[id_str]
                            except json.decoder.JSONDecodeError:
                                print("Received illegal payload")

                    else:
                        print("Received a followup-block with no entry in storage")

            else:
                self._publish(received_request)

    def _send_request_obj(self, req: Request, timeout: int = 6) -> Optional[Request]:
        self._logger.debug(f"Sending Request to '{req.get_path()}'")
        self._send_data(req)
        if timeout > 0:
            req_receiver = NetworkReceiver(self)
            responses = req_receiver.wait_for_responses(req, timeout)
            if not responses:
                return None
            return responses[0]

        return None

    def send_request(self, path: str, receiver: str, payload: dict, timeout: int = 6) -> Optional[Request]:
        """
        Sends a request and waits for a response by default.

        Returns the Ack-Status of the response, the status message of the response and the response itself.
        """
        req = Request(path, None, self._name, receiver, payload)
        return self._send_request_obj(req, timeout)

    def send_broadcast(self, path: str, payload: dict, timeout: int = 5,
                       max_responses: Optional[int] = None) -> list[Request]:
        req = Request(path, None, self._name, None, payload)
        self._send_data(req)
        req_receiver = NetworkReceiver(self)
        responses = req_receiver.wait_for_responses(req, timeout, max_responses)
        return responses

    def send_request_split(self, path: str, receiver: str, payload: dict, part_max_size: int = 30,
                           timeout: int = 6) -> Optional[Request]:
        req = Request(path, None, self._name, receiver, payload)
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
                res = self._send_request_obj(out_req, timeout)

                return res
            else:
                self._send_request_obj(out_req, 0)
            package_index += 1
            sleep(0.1)
        return None

    def respond(self, req: Request, payload: dict, path: Optional[str] = None):
        if path:
            out_path = path
        else:
            out_path = req.get_path()

        receiver = req.get_sender()

        out_req = Request(out_path,
                          req.get_session_id(),
                          self._name,
                          receiver,
                          payload)

        self._send_request_obj(out_req, 0)
