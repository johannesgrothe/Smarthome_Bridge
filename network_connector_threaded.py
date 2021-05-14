"""Module containing the ThreadedNetworkConnector class"""

from threading import Thread
from abc import ABC
from network_connector import NetworkConnector


class ThreadedNetworkConnector(NetworkConnector, ABC):
    """Class to implement an network interface prototype with a receive thread"""

    __receive_thread: Thread
    __thread_running: bool

    def __init__(self):
        super().__init__()
        self.__thread_running = True
        self.__receive_thread = Thread(target=self.__receive_thread)

    def __del__(self):
        self.__thread_running = False
        self.__receive_thread.join()

    def _start_thread(self):
        self.__receive_thread.start()

    def __receive_thread(self):
        self._logger.info("Launching receive thread")
        while self.__thread_running:
            self._receive()
        self._logger.info("Shutting down receive thread")
