"""Module for the SmarthomeClient Class"""
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

    # Flag to determine whether the client needs an update
    __needs_update: bool

    def __init__(self, name: str, runtime_id: int):
        self.__name = name
        self.__last_connected = 0
        self.__created: int(time())
        self.__runtime_id = runtime_id
        self.__needs_update = True

    def get_name(self):
        """Returns the name of the client"""
        return self.__name

    def get_created(self) -> int:
        """Gets the timestamp when the client was created in seconds since the epoch"""
        return self.__created

    def get_last_connected(self) -> int:
        """Returns when the client was last active in seconds since the epoch"""
        return self.__last_connected

    def trigger_activity(self):
        """Reports any activity of the client"""
        self.__last_connected = int(time())

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return self.__last_connected + max_timeout > int(time())

    def update_runtime_id(self, runtime_id: bool):
        """Updates the current runtime_id, sets internal 'needs_update'-flag if it changed"""
        if self.__runtime_id != runtime_id:
            self.__runtime_id = runtime_id
            self.__needs_update = True

    def needs_update(self) -> bool:
        """Returns whether the client needs an update from its hardware representation"""
        return self.__needs_update

    def report_update(self):
        """Reports an successful update to the client"""
        self.__needs_update = False
