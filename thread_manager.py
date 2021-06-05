import logging
from logging import Logger
from threading import Thread
from typing import Callable


class ThreadController:
    _thread: Thread
    _thread_running: bool

    def __init__(self, thread_method: Callable):
        self._thread_running = True
        self._thread = self._create_thread(thread_method)

    def _create_thread(self, thread_method: Callable) -> Thread:
        def buffer_thread_method():
            while self._thread_running:
                thread_method()

        buffer_thread = Thread(target=buffer_thread_method)

        return buffer_thread

    def start(self):
        self._thread_running = True
        self._thread.start()

    def kill(self):
        self._thread_running = False
        self._thread.join()


class ThreadManager:

    _logger: logging.Logger

    _threads: dict
    _threads: list[ThreadController]
    _threads_running: bool

    def __init__(self):
        self._logger = logging.getLogger("ThreadManager")
        self._threads = {}

    def __del__(self):
        self._remove_all_threads()

    def _remove_all_threads(self):
        self._threads_running = False
        for thread_id in self._threads:
            self.remove_thread(thread_id)

    def start_threads(self):
        self._threads_running = True
        for thread_id in self._threads:
            thread = self._threads[thread_id]
            if not thread.is_alive():
                self._logger.info("Launching Thread")
                thread.start()

    def add_thread(self, thread_id: str, thread_method: Callable) -> ThreadController:
        controller = ThreadController(thread_method)
        self._threads[thread_id] = controller
        return controller

    def remove_thread(self, thread_id: str):
        self._threads[thread_id].kill()
        del self._threads[thread_id]

    def get_thread(self, thread_id: str) -> ThreadController:
        return self._threads[thread_id]
