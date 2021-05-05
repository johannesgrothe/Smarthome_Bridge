import json
import logging
from request import Request
from typing import Optional
from queue import Queue
from datetime import datetime, timedelta
from time import sleep
from abc import abstractmethod, ABC, ABCMeta

Req_Response = tuple[Optional[bool], Optional[Request]]


class NetworkConnector(metaclass=ABCMeta):
    """Class to implement an network interface prototype"""

    _logger: logging.Logger
    _message_queue: Queue  # TODO: Make private
    _request_validation_schema: dict

    __part_data: dict

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.info(self.__class__.__name__)

        self._connected = False
        self._message_queue = Queue()
        self.__part_data = {}
        with open("json_schemas/request_basic_structure.json", "r") as f:
            self._request_validation_schema = json.load(f)

    @abstractmethod
    def _send_data(self, req: Request):
        print(f"Not implemented: '_send_data'")

    @abstractmethod
    def _receive_data(self) -> Optional[Request]:
        print(f"Not implemented: '_receive_data'")
        return None

    def get_request(self) -> Optional[Request]:
        """Returns a request if there is one"""

        if not self._message_queue.empty():
            return self._message_queue.get()
        return None

    def _receive(self):
        """Tries to receive a new request from the network and adds it to the queue"""
        received_request = self._receive_data()
        if received_request:
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
                        print("Received first block of split request without last_index")
                else:
                    if id_str in self.__part_data:
                        req_data = self.__part_data[id_str]
                        req_data["payload_bits"][p_index] = split_payload
                        if p_index >= req_data["last_index"]:
                            end_data = ""
                            for str_data in req_data["payload_bits"]:
                                if str_data is None:
                                    print("Detected missing data block")
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
                                self._message_queue.put(out_req)
                                del self.__part_data[id_str]
                            except json.decoder.JSONDecodeError:
                                print("Received illegal payload")

                    else:
                        print("Received a followup-block with no entry in storage")

            else:
                self._message_queue.put(received_request)

    def send_request(self, req: Request, timeout: int = 6) -> Req_Response:
        """
        Sends a request and waits for a response by default.

        Returns the Ack-Status of the response, the status message of the response and the response itself.
        """
        self._send_data(req)
        if timeout > 0:
            timeout_time = datetime.now() + timedelta(seconds=timeout)
            checked_requests_list = Queue()
            while datetime.now() < timeout_time:

                self.__receive()

                if not self._message_queue.empty():
                    res: Request = self._message_queue.get()
                    if res.get_session_id() == req.get_session_id() and req.get_sender() != res.get_sender():
                        res_ack = res.get_ack()

                        # Put checked requests back in queue
                        while not checked_requests_list.empty():
                            self._message_queue.put(checked_requests_list.get())

                        return res_ack, res

                    # Save request to put it back in queue later
                    checked_requests_list.put(res)

            # Put checked requests back in queue
            while not checked_requests_list.empty():
                self._message_queue.put(checked_requests_list.get())
            return None, None

        return None, None

    def send_broadcast(self, req: Request, timeout: int = 5) -> [Request]:
        responses: [Request] = []
        self._send_data(req)
        timeout_time = datetime.now() + timedelta(seconds=timeout)
        # checked_requests_list = Queue()
        while datetime.now() < timeout_time:
            if not self._message_queue.empty():
                res: Request = self._message_queue.get()
                # print("Got from Queue: {}".format(res.to_string()))
                if res.get_path() == "smarthome/broadcast/res" and res.get_session_id() == req.get_session_id():
                    responses.append(res)
        return responses

    def send_request_split(self, req: Request, part_max_size: int = 30, timeout: int = 6) -> Req_Response:
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
            if package_index == last_index:
                res_ack, res = self.send_request(out_req, timeout)

                return res_ack, res
            else:
                self.send_request(out_req, 0)
            package_index += 1
            sleep(0.1)
        return False, None

    @abstractmethod
    def connected(self) -> bool:
        print("!!Not implemented!!")
        return False
