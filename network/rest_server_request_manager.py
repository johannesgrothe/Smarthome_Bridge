import random
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta

from network.auth_container import CredentialsAuthContainer, AuthContainer
from network.request import Request, response_callback_type


class NoResponseReceivedError(Exception):
    def __init__(self, path: str):
        super().__init__(f"No Response received at path '{path}'")


class IllegalResponseException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class RestServerRequestManager:
    _request: Request
    _response: Optional[Request]

    def __init__(self, hostname: str, path: str, payload: dict, auth: Optional[AuthContainer]):
        self._response = None
        self._create_incoming_request(hostname, path, payload, auth)

    def __del__(self):
        pass

    def _create_incoming_request(self, hostname: str, path: str, payload: dict, auth: Optional[AuthContainer]):
        session_id = random.randint(0, 30000)
        sender = f"rest_client_{session_id}"
        self._request = Request(path=path,
                                session_id=session_id,
                                sender=sender,
                                receiver=hostname,
                                payload=payload,
                                is_response=False)
        if auth is not None:
            self._request.set_auth(auth)
        self._request.set_callback_method(self._get_response_function())

    def _get_response_function(self) -> response_callback_type:
        def respond(req: Request, payload: dict, path: Optional[str]):
            if req.get_session_id() != self._request.get_session_id():
                raise IllegalResponseException(f"Session IDs {req.get_session_id()} and "
                                               f"{self._request.get_session_id()} are not matching")
            if path is not None:
                res_path = path
            else:
                res_path = req.get_path()

            self._response = Request(path=res_path,
                                     session_id=req.get_session_id(),
                                     sender=self._request.get_receiver(),
                                     receiver=req.get_sender(),
                                     payload=payload,
                                     is_response=True)

        return respond

    def get_request(self) -> Request:
        return self._request

    def await_response(self, timeout: int = 2) -> Request:
        start_time = datetime.now()
        while self._response is None:
            time.sleep(0.1)
            now = datetime.now()
            if now > (start_time + timedelta(seconds=timeout)):
                break

        if self._response is None:
            raise NoResponseReceivedError(self._request.get_path())
        return self._response
