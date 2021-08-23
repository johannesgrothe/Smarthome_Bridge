from datetime import datetime, timedelta
from queue import Queue
from typing import Optional

from network.request import Request
from pubsub import Publisher, Subscriber


class NetworkReceiver(Subscriber):

    _request_queue: Queue
    _keep_queue: bool

    def __init__(self):
        super().__init__()
        self._request_queue = Queue()
        self._keep_queue = False

    def __del__(self):
        pass

    def receive(self, req: Request):
        print("received")
        self._request_queue.put(req)

    def start_listening_for_responses(self):
        """Clears the queue and starts recording requests.
        All received requests are used the next time wait_for_responses() is called."""
        self._request_queue = Queue()
        self._keep_queue = True

    def wait_for_responses(self, out_req: Request, timeout: int = 5,
                           max_resp_count: Optional[int] = 1) -> list[Request]:
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
