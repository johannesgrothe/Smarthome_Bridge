"""Module to contain the request class"""
from typing import Union, Optional


class Request:
    """Class to represent a network request"""

    __path: str
    __session_id: int
    __sender: str
    __receiver: Optional[str]
    __payload: dict

    def __init__(self, path: str, session_id: int, sender: str, receiver: Optional[str], payload: dict):
        """Constructor for the request"""

        if not path:
            raise RuntimeError("path cannot be empty")
        if not session_id:
            raise RuntimeError("session_id cannot be empty")
        if not sender:
            raise RuntimeError("sender cannot be empty")

        self.__path = path
        self.__session_id = session_id
        self.__sender = sender
        self.__receiver = receiver
        self.__payload = payload

    def get_path(self) -> str:
        """Returns the path"""

        return self.__path

    def get_session_id(self) -> int:
        """Returns the session id"""

        return self.__session_id

    def get_sender(self) -> str:
        """Returns the sender"""

        return self.__sender

    def get_receiver(self) -> str:
        """Returns the receiver"""

        return self.__receiver

    def get_payload(self) -> dict:
        """Returns the payload"""

        return self.__payload

    def get_body(self) -> dict:
        """Return the body"""

        return {"session_id": self.__session_id,
                "sender": self.__sender,
                "receiver": self.__receiver,
                "payload": self.__payload}

    def get_ack(self) -> Optional[bool]:
        """Returns the 'ack' if there is one in the payload and 'None' otherwise"""

        if "ack" in self.__payload:
            return self.__payload["ack"]
        return None

    def get_status_msg(self) -> Optional[str]:
        """Returns the 'status_msg' if there is one in the payload and 'None' otherwise"""

        if "status_msg" in self.__payload:
            return self.__payload["status_msg"]
        return None

    def get_response(self, ack: bool = None, payload: dict = None, path: str = None):  # -> Request:
        """Generates a response """

        if not path:
            new_path = self.__path
        else:
            new_path = path

        if not payload:
            new_payload = {}
        else:
            new_payload = payload

        if ack is not None:
            new_payload["ack"] = ack

        return Request(path=new_path,
                       session_id=self.__session_id,
                       sender=self.__receiver,
                       receiver=self.__sender,
                       payload=new_payload)
