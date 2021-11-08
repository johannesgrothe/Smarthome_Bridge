"""Module for the SmarthomeClient Class"""
from datetime import datetime, timedelta
from typing import Optional
from logging_interface import LoggingInterface

# Maximum timeout in seconds before the client is considered inactive
from smarthome_bridge.client_event_mapping import ClientEventMapping

DEFAULT_TIMEOUT = 17


class Client(LoggingInterface):
    """Smarthome client information"""

    # The name of the client
    _name: str

    # When the client was last connected
    _last_connected: datetime

    # When the client was created
    _created: datetime

    # A unique runtime id provided by the chip. Has to change on every reboot of the client
    _runtime_id: int

    # Date the chip was flashed (if available)
    _flash_time: Optional[datetime]

    # Software-commit hash
    _software_commit: Optional[str]

    # Branch the current software is on
    _software_branch: Optional[str]

    # Mapping for the ports on the client
    _port_mapping: dict

    # Event mapping of the client
    _event_mapping: list[ClientEventMapping]

    # Boot mode of the client
    _boot_mode: int

    def __init__(self, name: str, runtime_id: int, flash_date: Optional[datetime],
                 software_commit: Optional[str], software_branch: Optional[str],
                 port_mapping: dict, boot_mode: int, connection_timeout: int = DEFAULT_TIMEOUT):
        super().__init__()
        self._name = name
        self._last_connected = datetime(1900, 1, 1)
        self._created = datetime.now()
        self._runtime_id = runtime_id
        self._timeout = connection_timeout
        self._event_mapping = []

        if flash_date:
            self._flash_time = flash_date - timedelta(microseconds=flash_date.microsecond)
        else:
            self._flash_time = None

        self._software_commit = software_commit
        self._software_branch = software_branch

        # Set boot mode to "Unknown_Mode"
        self._boot_mode = boot_mode

        has_err, self._port_mapping = self._filter_mapping(port_mapping)
        if has_err:
            self._logger.warning(f"Detected problem in port mapping: '{port_mapping}'")

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, self.__class__):
            return self.get_name() == other.get_name() and \
                   self.get_runtime_id() == other.get_runtime_id() and \
                   self.get_sw_flash_time() == other.get_sw_flash_time() and \
                   self.get_sw_commit() == other.get_sw_commit() and \
                   self.get_sw_branch() == other.get_sw_branch() and \
                   self.get_boot_mode() == other.get_boot_mode() and \
                   self.get_port_mapping() == other.get_port_mapping()
        return NotImplemented

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
        return self._name

    def get_created(self) -> datetime:
        """Gets the timestamp when the client was created in seconds since the epoch"""
        return self._created

    def get_last_connected(self) -> datetime:
        """Returns when the client was last active in seconds since the epoch"""
        return self._last_connected

    def get_runtime_id(self) -> int:
        return self._runtime_id

    def trigger_activity(self):
        """Reports any activity of the client"""
        self._last_connected = datetime.now()

    def is_active(self) -> bool:
        """Returns whether the client is still considered active"""
        return self._last_connected + timedelta(seconds=self._timeout) > datetime.now()

    def update_runtime_id(self, runtime_id: int):
        """Updates the current runtime_id, sets internal 'needs_update'-flag if it changed"""
        self._runtime_id = runtime_id

    def get_port_mapping(self) -> dict:
        """Returns the port mapping of the client"""
        return self._port_mapping

    def get_sw_flash_time(self) -> Optional[datetime]:
        """Returns the date, the software was written on the chip"""
        return self._flash_time

    def get_sw_commit(self) -> Optional[str]:
        """Returns the software commit if available"""
        return self._software_commit

    def get_sw_branch(self) -> Optional[str]:
        """Returns the software branch name if available"""
        return self._software_branch

    def get_boot_mode(self) -> int:
        """Returns the boot mode of the chip"""
        return self._boot_mode

    def set_timeout(self, seconds: int):
        self._timeout = seconds

    def get_event_mapping(self) -> list[ClientEventMapping]:
        """Returns the configured event mapping of the client"""
        return self._event_mapping

    def set_event_mapping(self, e_mapping: list[ClientEventMapping]):
        self._event_mapping = e_mapping


