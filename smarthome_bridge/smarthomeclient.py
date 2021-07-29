"""Module for the SmarthomeClient Class"""
from datetime import datetime, timedelta
from typing import Optional
import logging

# Maximum timeout in seconds before the client is considered inactive
DEFAULT_TIMEOUT = 17


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

    __logger: logging.Logger

    def __init__(self, name: str, runtime_id: int, flash_date: Optional[datetime],
                 software_commit: Optional[str], software_branch: Optional[str],
                 port_mapping: dict, boot_mode: int, connection_timeout: int = DEFAULT_TIMEOUT):
        self.__name = name
        self.__last_connected = datetime(1900, 1, 1)
        self.__created = datetime.now()
        self.__runtime_id = runtime_id
        self._timeout = connection_timeout
        self._logger = logging.getLogger(self.__class__.__name__)

        self.__flash_time = flash_date
        self.__software_commit = software_commit
        self.__software_branch = software_branch

        # Set boot mode to "Unknown_Mode"
        self.__boot_mode = boot_mode

        has_err, self.__port_mapping = self._filter_mapping(port_mapping)
        if has_err:
            self._logger.warning(f"Detected problem in port mapping: '{port_mapping}'")

    def _filter_mapping(self, in_map: dict) -> (bool, dict):
        """Filters a port mapping dict to not contain any non-int or negative keys and no double values.

        Returns has_error, filtered_dict"""
        out_ports: dict = {}
        has_err: bool = False

        for key in in_map:
            try:
                if int(key) > 0:
                    val = in_map[key]
                    out_ports[key] = val
                else:
                    self._logger.error(f"Negative port number: '{key}'")
                    has_err = True
            except ValueError:
                self._logger.error(f"Illegal key: '{key}'")
                has_err = True
        return has_err, out_ports

    def get_name(self):
        """Returns the name of the client"""
        return self.__name

    def get_created(self) -> datetime:
        """Gets the timestamp when the client was created in seconds since the epoch"""
        return self.__created

    def get_last_connected(self) -> datetime:
        """Returns when the client was last active in seconds since the epoch"""
        return self.__last_connected

    def get_runtime_id(self) -> int:
        return self.__runtime_id

    def get_flash_date(self) -> datetime:
        return self.__flash_time

    def get_software_commit(self) -> str:
        return self.__software_commit

    def get_software_branch(self) -> str:
        return self.__software_branch

    def trigger_activity(self):
        """Reports any activity of the client"""
        self.__last_connected = datetime.now()

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return self.__last_connected + timedelta(seconds=self._timeout) > datetime.now()

    def update_runtime_id(self, runtime_id: int):
        """Updates the current runtime_id, sets internal 'needs_update'-flag if it changed"""
        self.__runtime_id = runtime_id

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

    def set_timeout(self, seconds: int):
        self._timeout = seconds
