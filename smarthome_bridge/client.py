"""Module for the SmarthomeClient Class"""
import threading
from datetime import datetime, timedelta
from typing import Optional

from gadgets.remote.remote_gadget import RemoteGadget
from lib.logging_interface import ILogging
from smarthome_bridge.client_information_interface import ClientInformationInterface
from system.utils.software_version import SoftwareVersion
from smarthome_bridge.client_event_mapping import ClientEventMapping

# Maximum timeout in seconds before the client is considered inactive
DEFAULT_TIMEOUT = 17


class ClientSoftwareInformationContainer:
    _commit: str
    _branch: str
    _date: datetime

    def __init__(self, commit: str, branch: str, date: datetime):
        self._commit = commit
        self._branch = branch
        self._date = date

    def __eq__(self, other) -> bool:
        if not isinstance(other, ClientSoftwareInformationContainer):
            return False
        return self.commit == other.commit and self.branch == other.branch and self.date == other.date

    @property
    def commit(self) -> str:
        return self._commit

    @property
    def branch(self) -> str:
        return self._branch

    @property
    def date(self) -> datetime:
        return self._date


class Client(ClientInformationInterface, ILogging):
    """Smarthome client information"""

    # The name of the client
    _id: str

    # When the client was last connected
    _last_connected: datetime

    # When the client was created
    _created: datetime

    # A unique runtime id provided by the chip. Has to change on every reboot of the client
    _runtime_id: int

    # Information about the software the client is running
    _software_info: Optional[ClientSoftwareInformationContainer]

    # Mapping for the ports on the client
    _port_mapping: dict

    # Event mapping of the client
    _event_mapping: list[ClientEventMapping]

    # Boot mode of the client
    _boot_mode: int

    # API version the client is running on
    _api_version: SoftwareVersion

    _gadgets: list[RemoteGadget]
    _gadgets_lock: threading.Lock

    def __init__(self, client_id: str, runtime_id: int, software: Optional[ClientSoftwareInformationContainer],
                 port_mapping: dict, boot_mode: int, api_version: SoftwareVersion,
                 connection_timeout: int = DEFAULT_TIMEOUT, gadgets: list[RemoteGadget] = None):
        super().__init__()
        self._id = client_id
        self._last_connected = datetime(1900, 1, 1)
        self._created = datetime.now()
        self._runtime_id = runtime_id
        self._timeout = connection_timeout
        self._api_version = api_version

        if gadgets is None:
            self._gadgets = []
        else:
            self._gadgets = gadgets
        self._gadgets_lock = threading.Lock()

        self._software_info = software

        # Set boot mode to "Unknown_Mode"
        self._boot_mode = boot_mode

        has_err, self._port_mapping = self._filter_mapping(port_mapping)
        if has_err:
            self._logger.warning(f"Detected problem in port mapping: '{port_mapping}'")

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, self.__class__):
            return self.id == other.id and \
                   self.runtime_id == other.runtime_id and \
                   self.software_info == other.software_info and \
                   self.boot_mode == other.boot_mode and \
                   self.get_port_mapping() == other.get_port_mapping() and \
                   self.api_version == other.api_version
        return NotImplemented

    def _filter_mapping(self, in_map: dict) -> (bool, dict):
        """
        Filters a port mapping dict to not contain any non-int or negative keys and no double values.

        :param in_map: Mapping dict to filter
        :return: has_error, filtered_dict
        """
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

    def _is_active(self) -> bool:
        return (self._last_connected + timedelta(seconds=self._timeout)) > datetime.now()

    def _get_id(self) -> str:
        return self._id

    @property
    def gadgets(self) -> list[RemoteGadget]:
        return self._gadgets

    @property
    def created(self) -> datetime:
        """The timestamp when the client was created in seconds since the epoch"""
        return self._created

    @property
    def last_connected(self) -> datetime:
        """When the client was last active in seconds since the epoch"""
        return self._last_connected

    @property
    def runtime_id(self) -> int:
        """The runtime if this client was using when last connected"""
        return self._runtime_id

    @property
    def software_info(self) -> Optional[ClientSoftwareInformationContainer]:
        """Information about the software the client is running"""
        return self._software_info

    @property
    def boot_mode(self) -> int:
        """The boot mode of the chip"""
        return self._boot_mode

    @property
    def api_version(self) -> SoftwareVersion:
        """The api version the client is running on"""
        return self._api_version

    def trigger_activity(self):
        """Reports any activity of the client"""
        self._last_connected = datetime.now()

    def get_port_mapping(self) -> dict:
        """Returns the port mapping of the client"""
        return self._port_mapping

    def set_timeout(self, seconds: int):
        """Sets the timeout for this client, after which it will register as 'offline'"""
        self._timeout = seconds
