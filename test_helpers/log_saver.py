import enum
import re
import datetime

from lib.logging_interface import LoggingInterface


class LogLevel(enum.Enum):
    fatal = "fatal"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


class LogMessage:
    timestamp: datetime.datetime
    level: LogLevel
    trigger_location: str
    trigger_method: str
    message: str

    def __init__(self, timestamp: datetime.datetime, level: LogLevel, location: str, method: str, message: str):
        self.timestamp = timestamp
        self.level = level
        self.trigger_location = location
        self.trigger_method = method
        self.message = message


class LogMessageFormatter:

    @staticmethod
    def get_csv_header():
        return ", ".join(["timestamp", "level", "location", "method", "message"]) + "\n"

    @staticmethod
    def msg_to_csv(message: LogMessage):
        level = message.level.value
        timestamp = str(message.timestamp)
        return ", ".join([timestamp, level, message.trigger_location, message.trigger_method, message.message]) + "\n"


class LogSaver(LoggingInterface):
    _messages: list[LogMessage]

    def __init__(self):
        super().__init__()
        self._messages = []

    def get_log_messages(self) -> list[LogMessage]:
        return self._messages

    def add_log_string(self, line: str):
        line = line.strip("\n").strip("\r").strip("\n")

        data = re.findall("\[(.)\]\[(.+?)\] (.+?): (.+)", line)
        if not data:
            self._logger.debug(f"Cannot decode line '{line}'")
            return
        data = data[0]

        switcher = {
            "E": LogLevel.error,
            "I": LogLevel.info,
            "W": LogLevel.warning,
            "D": LogLevel.debug
        }

        level = switcher.get(data[0], None)

        if level is None:
            self._logger.error(f"Cannot decode log level '{data[0]}'")
            return

        buf_msg = LogMessage(datetime.datetime.now(), level, data[1], data[2], data[3])
        self.add_log_message(buf_msg)

    def add_log_message(self, message: LogMessage):
        self._messages.append(message)

    def save(self, path: str):
        ending = path.split(".")[-1]
        if ending == "csv":
            lines = [LogMessageFormatter.get_csv_header()] + [LogMessageFormatter.msg_to_csv(x) for x in self._messages]
        else:
            raise Exception(f"Unknown file encoding '{ending}'")

        with open(path, "w") as file_p:
            file_p.writelines(lines)
