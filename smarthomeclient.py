"""Module for the SmarthomeCLient Class"""
from time import time

# Maximum timeout before the client is considered inactive
max_timeout = 15000


class SmarthomeClient:
    """Smarthome client information"""

    __name: str
    __last_connected: int

    def __init__(self, name: str):
        self.__name = name
        self.__last_connected = 0

    def get_name(self):
        """Returns the name of the client"""
        return self.__name

    def get_last_connected(self) -> int:
        """Returns when the client was last active in seconds since the epoch"""
        return self.__last_connected

    def trigger_activity(self):
        """Reports any activity of the client"""
        self.__last_connected = int(time())

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return last_connected + max_timeout > int(time())
