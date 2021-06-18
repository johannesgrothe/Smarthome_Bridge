import logging
from abc import abstractmethod
from queue import Queue
from typing import Optional

from json_validator import Validator
from network.request import Request, response_callback_type
from network.split_request_handler import SplitRequestHandler
from pubsub import Publisher
from thread_manager import ThreadManager


class ClientDisconnectedException(Exception):
    def __init__(self, address: str):
        super().__init__(f"Client with the Address '{address}' is disconnected")


class NetworkServerClient(Publisher):
    _host_name: str
    _address: str
    _response_method: response_callback_type
    _validator: Validator
    _logger: logging.Logger

    _thread_manager: ThreadManager

    __split_handler: SplitRequestHandler

    __out_queue: Queue
    __in_queue: Queue

    def __init__(self, host_name: str, address: str):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._address = address
        self._validator = Validator()

        self.__split_handler = SplitRequestHandler()

        self.__out_queue = Queue()
        self.__in_queue = Queue()

        self._thread_manager = ThreadManager()
        self._thread_manager.add_thread("send_thread", self.__task_send)
        self._thread_manager.add_thread("receive_thread", self.__task_receive)

    def __del__(self):
        self._thread_manager.__del__()

    def __task_send(self):
        if not self.__out_queue.empty():
            out_req = self.__out_queue.get()
            self._send(out_req)

    def __task_receive(self):
        in_req = self._receive()
        if in_req:
            req = self.__split_handler.handle(in_req)
            if req:
                req.set_callback_method(self._respond_to)
                self._publish(req)

    def _respond_to(self, req: Request, payload: dict, path: Optional[str] = None):
        if path:
            out_path = path
        else:
            out_path = req.get_path()

        receiver = req.get_sender()

        out_req = Request(out_path,
                          req.get_session_id(),
                          self._host_name,
                          receiver,
                          payload)

        self._send(out_req)

    def _forward_request(self, req: Request):
        self._logger.info(f"Received Request at '{req.get_path()}'")
        self._publish(req)

    def send_request(self, req: Request):
        self.__out_queue.put(req)

    @abstractmethod
    def _send(self, req: Request):
        pass

    @abstractmethod
    def _receive(self) -> Optional[Request]:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    def get_address(self) -> str:
        return self._address
