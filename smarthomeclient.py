"""Module for the SmarthomeCLient Class"""
from time import time

# Maximum timeout before the client is considered inactive
max_timeout = 15000


class SmarthomeClient:
    """Smarthome client information"""

    # The name of the client
    __name: str

    # When the client was last connected
    __last_connected: int

    # When the client was created
    __created: int

    # A unique runtime id provided by the chip. Has to change on every reboot of the client
    __runtime_id: int

    def __init__(self, name: str, runtime_id: int):
        self.__name = name
        self.__last_connected = 0
        self.__created: int(time())
        self.__runtime_id = runtime_id

    def get_name(self):
        """Returns the name of the client"""
        return self.__name

    def get_created(self) -> int:
        """Gets the timestamd when the client was created in seconds since the epoch"""
        return self.__created

    def get_last_connected(self) -> int:
        """Returns when the client was last active in seconds since the epoch"""
        return self.__last_connected

    def trigger_activity(self):
        """Reports any activity of the client"""
        self.__last_connected = int(time())

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return last_connected + max_timeout > int(time())
