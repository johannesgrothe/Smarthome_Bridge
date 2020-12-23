"""Module for the SmarthomeClient Class"""
from time import time
from datetime import datetime
from typing import Optional

# Maximum timeout in seconds before the client is considered inactive
max_timeout = 17


def filter_mapping(in_map: dict) -> (bool, dict):
    """Filters a port mapping dict to not contain any non-int or negative keys and no double values.

    Returns has_error, filtered_dict"""
    port_list: [str] = []
    out_ports: dict = {}
    has_err: bool = False

    for key in in_map:
        try:
            if int(key) > 0:
                val = in_map[key]
                if val in port_list:
                    print("error double port usage")
                    has_err = True
                else:
                    port_list.append(val)
                    out_ports[key] = val
            else:
                print("Negative port number: '{}'".format(key))
                has_err = True
        except ValueError:
            print("Illegal key: '{}'".format(key))
            has_err = True
    return has_err, out_ports


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

    # Date the chip was flashed (if available)
    __flash_date: Optional[datetime]

    # Software-commit hash
    __software_commit: Optional[str]

    # Branch the current software is on
    __software_branch: Optional[str]

    # Mapping for the ports on the client
    __port_mapping: dict

    def __init__(self, name: str, runtime_id: int):
        self.__name = name
        self.__last_connected = 0
        self.__created = int(time())
        self.__runtime_id = runtime_id
        self.__needs_update = True

        self.__flash_date = None
        self.__software_commit = None
        self.__software_branch = None

        has_err, self.__port_mapping = filter_mapping({})

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

    def update_data(self, flash_date: Optional[datetime], software_commit: Optional[str],
                    software_branch: Optional[str], port_mapping: dict):
        """Reports an successful update to the client"""

        self.__flash_date = datetime.strptime(flash_date, "%Y-%m-%d")
        self.__software_commit = software_commit
        self.__software_branch = software_branch

        has_err, self.__port_mapping = filter_mapping(port_mapping)

        self.__needs_update = False

    def serialized(self) -> dict:
        """Returns a serialized version of the client"""
        out_date = None
        if self.__flash_date is not None:
            out_date = str(self.__flash_date.date())

        return {"name": self.__name,
                "created": self.__created,
                "last_connected": self.__last_connected,
                "is_active": self.is_active(),
                "sw_uploaded": out_date,
                "sw_version": self.__software_commit,
                "sw_branch": self.__software_branch,
                "port_mapping": self.__port_mapping}

    def get_port_mapping(self) -> dict:
        """Returns the port mapping of the client"""
        return self.__port_mapping

    def get_sw_flash_date(self) -> Optional[datetime]:
        """Returns the date, the software was written on the chip"""
        return self.__flash_date

    def get_sw_commit(self) -> Optional[str]:
        """Returns the software commit if available"""
        return self.__software_commit

    def get_sw_branch(self) -> Optional[str]:
        """Returns the software branch name if available"""
        return self.__software_branch
