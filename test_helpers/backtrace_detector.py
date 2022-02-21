"""Module for the BacktraceDetector"""
import datetime
from typing import Tuple

from lib.logging_interface import LoggingInterface


class BacktraceDetector(LoggingInterface):
    """Class that reads log messages, detects backtraces, stores them and provides
    runtime information about backtraces found"""
    _backtraces = list[Tuple[str, str]]

    def __init__(self):
        super().__init__()
        self._backtraces = []

    def check_line(self, line: str):
        """
        Checks a line for backtraces to store

        :param line: Line to check
        :return: None
        """
        if line.startswith("Backtrace: 0x"):
            self._logger.info(f"Backtrace Detected: '{line}'")
            self._backtraces.append((datetime.datetime.now(), line))

    def get_backtrace_count(self) -> int:
        """
        Provides information about how many crash-backtraces were detected

        :return: Count of the detected backtraces
        """
        return len(self._backtraces)

    def save(self, path: str):
        """
        Stores the detected backtraces away in a CSV

        :param path: Path to save the file at
        :return: None
        """
        self._logger.info(f"Saving backtrace log with {len(self._backtraces)} entries at '{path}'")
        ending = path.split(".")[-1]
        if ending == "csv":
            lines = ["timestamp, backtrace\n"] + [f"{a}, {b}\n" for a, b in self._backtraces]
        else:
            raise Exception(f"Unknown file encoding '{ending}'")

        with open(path, "w") as file_p:
            file_p.writelines(lines)
