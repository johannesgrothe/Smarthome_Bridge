from network.network_connector import NetworkConnector
from network.request import Request
from typing import Optional
import threading
import time


class DummyNetworkConnector(NetworkConnector):

    _mock_ack: Optional[bool]
    _last_send: Optional[Request]

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self._mock_ack = None
        self._last_send = None

    def __del__(self):
        super().__del__()

    def _respond_with_ack(self, req: Request):
        def thread_method():
            time.sleep(1)
            out_req = Request(req.get_path(),
                              req.get_session_id(),
                              req.get_receiver(),
                              req.get_sender(),
                              {"ack": self._mock_ack})
            self.receive(out_req)

        if self._mock_ack is not None:
            t = threading.Thread(target=thread_method)
            t.start()

    def _send_data(self, req: Request):
        self._last_send = req
        self._respond_with_ack(req)

    def mock_ack(self, ack: Optional[bool]):
        """Makes connector respond to every send request with the selected ack.
        Pass 'None' or use the reset() function to stop replying with any ack at all"""
        self._mock_ack = ack

    def get_last_send_req(self) -> Optional[Request]:
        return self._last_send

    def mock_receive(self, path: str, sender: str, payload: dict):
        buf_req = Request(path,
                          None,
                          sender,
                          self._hostname,
                          payload)
        self.receive(buf_req)

    def reset(self):
        """Resets the mocking behaviour of this connector"""
        self._mock_ack = None
        self._last_send = None
