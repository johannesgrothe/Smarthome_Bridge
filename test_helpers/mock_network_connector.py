from network.network_connector import NetworkConnector
from datetime import datetime, timedelta
import time
from network.request import Request
from typing import Optional
import threading


class MockNetworkConnector(NetworkConnector):

    _mock_ack: Optional[bool]
    _thread_request: Optional[Request]
    _run_thread: bool
    _response_thread: Optional[threading.Thread]

    def __init__(self, hostname: str):
        super().__init__(hostname)
        self._run_thread = False
        self._mock_ack = None
        self._response_thread = None
        self._thread_request = None

    def __del__(self):
        super().__del__()
        self._stop_response_thread()

    def _stop_response_thread(self):
        self._run_thread = False
        if self._response_thread is not None:
            self._response_thread.join()
            self._response_thread = None

    def _thread_function(self):
        start = datetime.now()
        time.sleep(0.1)
        while self._run_thread and (start + timedelta(seconds=10) > datetime.now()):
            if self._mock_ack is not None:
                out_req = Request(self._thread_request.get_path(),
                                  self._thread_request.get_session_id(),
                                  self._thread_request.get_receiver(),
                                  self._thread_request.get_sender(),
                                  {"ack": self._mock_ack})
                self.receive(out_req)

    def _start_response_thread(self, req: Request):

        self._stop_response_thread()

        self._thread_request = req
        self._run_thread = True
        self._response_thread = threading.Thread(target=self._thread_function)
        self._response_thread.start()

    def _send_data(self, req: Request):
        self._start_response_thread(req)

    def mock_ack(self, ack: bool):
        """Makes connector respond to every send request with the selected ack.
        Pass 'None' or use the reset() function to stop replying with any ack at all"""
        self._mock_ack = ack

    def reset(self):
        """Resets the mocking behaviour of this connector"""
        self._mock_ack = None
        self._stop_response_thread()
