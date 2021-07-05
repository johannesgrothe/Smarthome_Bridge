"""Module to contain the request class"""
from __future__ import annotations
import random
from typing import Optional, Callable


class NoClientResponseException(Exception):
    def __init__(self):
        super().__init__("NoClientResponseException: No Client answered to the Request sent")


class NoResponsePossibleException(Exception):
    def __init__(self):
        super().__init__("Responding is not possible because there is no function set.")


def generate_request_id() -> int:
    """Generates a random Request ID"""

    return random.randint(0, 1000000)


class Request:
    """Class to represent a network request"""

    _path: str
    _session_id: int
    _sender: str
    _receiver: Optional[str]
    _payload: dict
    _response_function: Optional[response_callback_type]
    _connection_type: Optional[str]

    def __init__(self, path: str, session_id: Optional[int], sender: str, receiver: Optional[str],
                 payload: dict, connection_type: Optional[str] = None):
        """Constructor for the request"""

        if not path:
            raise RuntimeError("path cannot be empty")
        if not sender:
            raise RuntimeError("sender cannot be empty")

        if not session_id:
            self._session_id = generate_request_id()
        else:
            self._session_id = session_id

        self._path = path
        self._sender = sender
        self._receiver = receiver
        self._payload = payload
        self._response_function = None
        self._connection_type = connection_type

    def set_callback_method(self, function: response_callback_type):
        self._response_function = function

    def respond(self, payload: dict, path: Optional[str] = None):
        if self._response_function is None:
            raise NoResponsePossibleException
        self._response_function(self, payload, path)

    def get_path(self) -> str:
        """Returns the path"""

        return self._path

    def get_session_id(self) -> int:
        """Returns the session id"""

        return self._session_id

    def get_sender(self) -> str:
        """Returns the sender"""

        return self._sender

    def get_receiver(self) -> str:
        """Returns the receiver"""

        return self._receiver

    def get_payload(self) -> dict:
        """Returns the payload"""

        return self._payload

    def get_body(self) -> dict:
        """Return the body"""

        return {"session_id": self._session_id,
                "sender": self._sender,
                "receiver": self._receiver,
                "payload": self._payload}

    def get_callback(self) -> response_callback_type:
        return self._response_function

    def get_ack(self) -> Optional[bool]:
        """Returns the 'ack' if there is one in the payload and 'None' otherwise"""

        if "ack" in self._payload:
            return self._payload["ack"]
        return None

    def get_status_msg(self) -> Optional[str]:
        """Returns the 'status_msg' if there is one in the payload and 'None' otherwise"""

        if "status_msg" in self._payload:
            return self._payload["status_msg"]
        return None

    def to_string(self) -> str:
        """Converts the request to a string"""
        return "<'{}': {}>".format(self.get_path(), self.get_body())


response_callback_type = Callable[[Request, dict, Optional[str]], None]
