from network.auth_container import AuthContainer
from network.network_connector import NetworkConnector
from network.request import Request
from typing import Optional
import threading
import time


class DummyNetworkConnector(NetworkConnector):
    _mock_ack: Optional[bool]
    _last_send: Optional[Request]
    _last_response: Optional[Request]

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self.reset()

    def __del__(self):
        super().__del__()

    def _respond_with_ack(self, req: Request):
        def thread_method():
            time.sleep(1)
            out_req = Request(req.get_path(),
                              req.get_session_id(),
                              req.get_receiver(),
                              req.get_sender(),
                              {"ack": self._mock_ack},
                              is_response=True)
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

    def get_last_send_response(self) -> Optional[Request]:
        return self._last_response

    def _get_mock_response_function(self):
        def mock_response_function(req: Request, payload: dict, path: str):
            if path is None:
                buf_path = req.get_path()
            else:
                buf_path = path
            out_req = Request(path=buf_path,
                              session_id=req.get_session_id(),
                              sender=req.get_receiver(),
                              receiver=req.get_sender(),
                              payload=payload,
                              is_response=True)
            self._last_response = out_req

        return mock_response_function

    def mock_receive(self, path: str, sender: str, payload: dict, is_response: bool = False,
                     auth: Optional[AuthContainer] = None):
        buf_req = Request(path,
                          None,
                          sender,
                          self._hostname,
                          payload,
                          is_response=is_response)
        buf_req.set_callback_method(self._get_mock_response_function())
        if auth:
            buf_req.set_auth(auth)
        self.receive(buf_req)

    def reset(self):
        """Resets the mocking behaviour of this connector"""
        self._mock_ack = None
        self._last_send = None
        self._last_response = None
