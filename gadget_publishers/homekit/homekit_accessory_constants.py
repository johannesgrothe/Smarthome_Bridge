import os

from utils.repository_manager import RepositoryManager

MANUFACTURER = "johannes_grothe"
HOMEKIT_SERVER_NAME = "HomekitAccessoryServer"
DUMMY_REVISION = "1.0.0"
_revision = None
_serial_number = 1


class HomekitConstants:
    _revision: str

    def __init__(self):
        # global _revision
        # if _revision is None:
        #     repo_manager = RepositoryManager(os.getcwd(), None)
        #     _revision = repo_manager.get_commit_hash()
        # self._revision = _revision
        self._revision = DUMMY_REVISION

    @property
    def manufacturer(self) -> str:
        return MANUFACTURER

    @property
    def serial_number(self) -> str:
        global _serial_number
        buf_nr = _serial_number
        _serial_number += 1
        return str(buf_nr)

    @property
    def revision(self) -> str:
        return self._revision

    @property
    def server_name(self) -> str:
        return HOMEKIT_SERVER_NAME
