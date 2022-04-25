MANUFACTURER = "johannes_grothe"
HOMEKIT_SERVER_NAME = "HomekitAccessoryServer"
DUMMY_REVISION = "1.0.0"
_revision = None
_serial_number = 1


class HomekitConstants:
    """Class to access constants for the homekit accessories/server"""
    _revision: str

    def __init__(self):
        """Constructor for the HomekitConstants container class"""
        # global _revision
        # if _revision is None:
        #     repo_manager = RepositoryManager(os.getcwd(), None)
        #     _revision = repo_manager.get_commit_hash()
        # self._revision = _revision
        self._revision = DUMMY_REVISION

    @property
    def manufacturer(self) -> str:
        """Manufacturer of the homekit device"""
        return MANUFACTURER

    @property
    def serial_number(self) -> str:
        """Serial number of the homekit device. Starts at 1 and increments on every access of this property"""
        global _serial_number
        buf_nr = _serial_number
        _serial_number += 1
        return str(buf_nr)

    @property
    def revision(self) -> str:
        """Software revision number of this homekit device"""
        return self._revision

    @property
    def server_name(self) -> str:
        """Name of the homekit server (bridge)"""
        return HOMEKIT_SERVER_NAME
