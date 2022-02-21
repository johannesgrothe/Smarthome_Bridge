import datetime
from typing import Tuple

from lib.logging_interface import LoggingInterface


class BacktraceDetector(LoggingInterface):
    _backtraces = list[Tuple[str, str]]

    def __init__(self):
        super().__init__()
        self._backtraces = []

    def check_line(self, line: str):
        if line.startswith("Backtrace: 0x"):
            self._logger.info(f"Backtrace Detected: '{line}'")
            self._backtraces.append((datetime.datetime.now(), line))

    def get_backtrace_count(self) -> int:
        return len(self._backtraces)

    def save(self, path: str):
        ending = path.split(".")[-1]
        if ending == "csv":
            lines = ["timestamp, backtrace\n"] + [f"{a}, {b}\n" for a, b in self._backtraces]
        else:
            raise Exception(f"Unknown file encoding '{ending}'")

        with open(path, "w") as file_p:
            file_p.writelines(lines)
