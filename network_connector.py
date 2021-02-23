from request import Request
from typing import Optional

Req_Response: tuple[Optional[bool], Optional[Request]]


class NetworkConnector:
    """Class to implement an network interface prototype"""

    __connected: bool

    def __init__(self):
        self.__connected = False

    def send_request(self, req: Request, timeout: int = 6) -> Req_Response:
        print("Not implemented")
        return None, None

    def send_broadcast(self, req: Request, timeout: int = 5) -> [Request]:
        print("Not implemented")
        return []

    def send_request_splitted(self, req: Request, part_max_size: int = 30, timeout: int = 6) -> Req_Response:
        session_id: int = req.get_session_id(),
        path: str = req.get_path()
        sender: Optional[str] = req.get_sender()
        receiver: Optional[str] = req.get_receiver(),

        payload_str = json.dumps(req.get_payload())
        payload_len = len(payload_str)
        parts = []
        start = 0
        package_index = 0

        while start < payload_len:
            end = start + part_max_size
            payload_part = payload_str[start:(end if end < payload_len else payload_len)]
            parts.append(payload_part)
            start = end + 1

        for payload_part in parts:

            out_dict = {"package_index": package_index, "split_payload": payload_part}
            if package_index == 0:
                out_dict["last_index"] = len(parts)

            out_req = Request(path,
                              session_id,
                              sender,
                              receiver,
                              out_dict)
            if package_index == len(parts):
                res_ack, res = self.send_request(out_req, timeout)
                return res_ack, res
            else:
                self.send_request(out_req, 0)

    def connected(self) -> bool:
        return self.__connected
