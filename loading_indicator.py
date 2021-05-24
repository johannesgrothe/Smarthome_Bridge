import threading
import time
from typing import Optional


class LoadingIndicator:

    _running: bool
    _run_thread: Optional[threading.Thread]

    def __init__(self):
        self._running = False
        self._run_thread = None

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _thread_runner(self):
        while self._running:
            print(".", end="")
            time.sleep(0.25)

    def _stop_thread(self):
        self._running = False
        if self._run_thread:
            self._run_thread.join()

    def run(self):
        self._stop_thread()

        print("[", end="")
        self._running = True
        self._run_thread = threading.Thread(target=self._thread_runner)
        self._run_thread.start()

    def stop(self):
        if self._running:
            print("]")
            self._stop_thread()