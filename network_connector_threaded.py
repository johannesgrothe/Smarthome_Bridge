"""Module containing the ThreadedNetworkConnector class"""
from threading import Thread
from abc import ABC
from network_connector import NetworkConnector, Request, response_callback_type  # Passed down to subclasses
from typing import Callable


class ThreadedNetworkConnector(NetworkConnector, ABC):
    """Class to implement an network interface prototype with a receive thread"""

    __threads: list[Thread]
    __threads_running: bool

    def __init__(self, name: str):
        super().__init__(name)
        self.__threads = []
        self._add_thread(self._receive)

    def __del__(self):
        self.__close_all_threads()

    def __close_all_threads(self):
        self.__threads_running = False
        for thread in self.__threads:
            thread.join()

    def _start_threads(self):
        self.__threads_running = True
        for thread in self.__threads:
            if not thread.is_alive():
                self._logger.info("Launching Thread")
                thread.start()

    def _add_thread(self, thread_method: Callable) -> Thread:
        def buffer_thread_method():
            while self.__threads_running:
                thread_method()

        buffer_thread = Thread(target=buffer_thread_method)
        self.__threads.append(buffer_thread)
        return buffer_thread
