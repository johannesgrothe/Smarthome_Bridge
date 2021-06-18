import json
import logging
from typing import Optional

from network.request import Request


class SplitRequestHandler:
    _logger: logging.Logger
    _part_data: dict

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._part_data = {}

    def handle(self, req: Request) -> Optional[Request]:
        self._logger.info(f"Received Request at '{req.get_path()}': {req.get_payload()}")
        req_payload = req.get_payload()
        if "package_index" in req_payload and "split_payload" in req_payload:
            return self._handle_split_request(req)
        else:
            return req

    def _handle_split_request(self, received_request: Request):
        req_payload = received_request.get_payload()
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
                self._part_data[id_str] = buf_json
            else:
                self._logger.error("Received first block of split request without last_index")
        else:
            if id_str in self._part_data:
                req_data = self._part_data[id_str]
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

                        out_req.set_callback_method(first_req.get_callback())
                        del self._part_data[id_str]
                        return out_req

                    except json.decoder.JSONDecodeError:
                        self._logger.error("Received illegal payload")

            else:
                self._logger.error("Received a followup-block with no entry in storage")
        return None
