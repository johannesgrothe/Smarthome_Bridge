import logging
from logging import Logger
from threading import Thread
from typing import Callable


class ThreadManager:

    _logger: logging.Logger

    _threads: dict
    _threads: list[Thread]
    _threads_running: bool

    def __init__(self):
        self._logger = logging.getLogger("ThreadManager")
        self._threads = {}

    def __del__(self):
        self._close_all_threads()

    def _close_all_threads(self):
        self._threads_running = False
        for thread_id in self._threads:
            thread = self._threads[thread_id]
            thread.join()

    def start_threads(self):
        self._threads_running = True
        for thread_id in self._threads:
            thread = self._threads[thread_id]
            if not thread.is_alive():
                self._logger.info("Launching Thread")
                thread.start()

    def add_thread(self, thread_id: str, thread_method: Callable):
        def buffer_thread_method():
            while self._threads_running:
                thread_method()

        buffer_thread = Thread(target=buffer_thread_method)

        self._threads[thread_id] = buffer_thread
        return buffer_thread

    def get_thread(self, thread_id: str):
        return self._threads[thread_id]
