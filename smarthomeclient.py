"""Module for the SmarthomeClient Class"""
from datetime import datetime, timedelta
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
    __last_connected: datetime

    # When the client was created
    __created: datetime

    # A unique runtime id provided by the chip. Has to change on every reboot of the client
    __runtime_id: int

    # Flag to determine whether the client needs an update
    __needs_update: bool

    # Date the chip was flashed (if available)
    __flash_time: Optional[datetime]

    # Software-commit hash
    __software_commit: Optional[str]

    # Branch the current software is on
    __software_branch: Optional[str]

    # Mapping for the ports on the client
    __port_mapping: dict

    # Boot mode of the client
    __boot_mode: int

    def __init__(self, name: str, runtime_id: int):
        self.__name = name
        self.__last_connected = datetime(1900, 1, 1)
        self.__created = datetime.now()
        self.__runtime_id = runtime_id
        self.__needs_update = True

        self.__flash_time = None
        self.__software_commit = None
        self.__software_branch = None

        # Set boot mode to "Unknown_Mode"
        self.__boot_mode = 3

        has_err, self.__port_mapping = filter_mapping({})

    def get_name(self):
        """Returns the name of the client"""
        return self.__name

    def get_created(self) -> datetime:
        """Gets the timestamp when the client was created in seconds since the epoch"""
        return self.__created

    def get_last_connected(self) -> datetime:
        """Returns when the client was last active in seconds since the epoch"""
        return self.__last_connected

    def trigger_activity(self):
        """Reports any activity of the client"""
        self.__last_connected = datetime.now()

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return self.__last_connected + timedelta(seconds=max_timeout) > datetime.now()

    def update_runtime_id(self, runtime_id: bool):
        """Updates the current runtime_id, sets internal 'needs_update'-flag if it changed"""
        if self.__runtime_id != runtime_id:
            self.__runtime_id = runtime_id
            self.__needs_update = True

    def needs_update(self) -> bool:
        """Returns whether the client needs an update from its hardware representation"""
        return self.__needs_update

    def update_data(self, flash_date: Optional[datetime], software_commit: Optional[str],
                    software_branch: Optional[str], port_mapping: dict, boot_mode: int):
        """Reports an successful update to the client"""

        self.__flash_time = datetime.strptime(flash_date, "%Y-%m-%d %H:%M:%S")
        self.__software_commit = software_commit
        self.__software_branch = software_branch
        self.__boot_mode = boot_mode

        has_err, self.__port_mapping = filter_mapping(port_mapping)
        if has_err:
            print(f"WARNING: PROBLEM FOUND IN PORT MAPPING '{port_mapping}'")

        self.__needs_update = False

    def serialized(self) -> dict:
        """Returns a serialized version of the client"""
        out_date = None
        if self.__flash_time is not None:
            out_date = self.__flash_time.strftime("%Y-%m-%d %H:%M:%S")

        return {"name": self.__name,
                "created": self.__created.strftime("%Y-%m-%d %H:%M:%S"),
                "last_connected": self.__last_connected.strftime("%Y-%m-%d %H:%M:%S"),
                "is_active": self.is_active(),
                "boot_mode": self.__boot_mode,
                "sw_uploaded": out_date,
                "sw_version": self.__software_commit,
                "sw_branch": self.__software_branch,
                "port_mapping": self.__port_mapping}

    def get_port_mapping(self) -> dict:
        """Returns the port mapping of the client"""
        return self.__port_mapping

    def get_sw_flash_time(self) -> Optional[datetime]:
        """Returns the date, the software was written on the chip"""
        return self.__flash_time

    def get_sw_commit(self) -> Optional[str]:
        """Returns the software commit if available"""
        return self.__software_commit

    def get_sw_branch(self) -> Optional[str]:
        """Returns the software branch name if available"""
        return self.__software_branch

    def get_boot_mode(self) -> int:
        """Returns the boot mode of the chip"""
        return self.__boot_mode
