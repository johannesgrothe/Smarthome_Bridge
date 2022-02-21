"""Module for the LogSaver and its utility classes"""
import enum
import re
import datetime

from lib.logging_interface import LoggingInterface


class LogLevel(enum.Enum):
    """Represents a log message severity level"""
    fatal = "fatal"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


class LogMessage:
    """Container for log message data"""
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


class LogMessageTXTFormatter:
    """Utility class to format log messages back to txt"""

    @staticmethod
    def parse_line(message: LogMessage):
        """
        Generates the txt line representation from a log message object

        :param message: Log message object to parse
        :return: The txt formatted line
        """
        switcher = {
            LogLevel.error: "E",
            LogLevel.info: "I",
            LogLevel.warning: "W",
            LogLevel.debug: "D"
        }

        level = switcher.get(message.level)
        return f"[{level}][{message.trigger_location}] {message.trigger_method}: {message.message}"


class LogMessageCSVFormatter:
    """Utility class to format log messages to csv"""

    @staticmethod
    def get_header():
        """
        Generates the fitting header for a csv output

        :return: The csv header
        """
        return ", ".join(["timestamp", "level", "location", "method", "message"]) + "\n"

    @staticmethod
    def parse_line(message: LogMessage):
        """
        Generates the csv line representation from a log message object

        :param message: Log message object to parse
        :return: The csv formatted line
        """
        level = message.level.value
        timestamp = str(message.timestamp)
        return ", ".join([timestamp, level, message.trigger_location, message.trigger_method, message.message]) + "\n"


class LogSaver(LoggingInterface):
    """Collects, decodes and stores log messages"""
    _messages: list[LogMessage]

    def __init__(self):
        super().__init__()
        self._messages = []

    def get_log_messages(self) -> list[LogMessage]:
        """
        Returns the received log message lines

        :return: The received messages
        """
        return self._messages

    def add_log_string(self, line: str):
        """
        Parses and stores a log message line

        :param line: The line containing the log message to store
        :return: None
        """
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
        """
        Adds a log message

        :param message: Log message to add
        :return: None
        """
        self._messages.append(message)

    def save(self, path: str):
        """Saves the log messages into a file"""
        ending = path.split(".")[-1]
        if ending == "csv":
            lines = [LogMessageCSVFormatter.get_header()] + [LogMessageCSVFormatter.parse_line(x)
                                                             for x
                                                             in self._messages]
        elif ending == "txt":
            lines = [LogMessageTXTFormatter.parse_line(x)
                     for x
                     in self._messages]
        else:
            raise Exception(f"Unknown file encoding '{ending}'")

        with open(path, "w") as file_p:
            file_p.writelines(lines)
