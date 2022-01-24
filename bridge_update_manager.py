import os
from typing import Optional, Tuple, Union
from repository_manager import RepositoryManager, RepositoryFetchException, RepositoryStatusException, \
    RepositoryCloneException


class UpdateNotSuccessfulException(Exception):
    def __init__(self):
        super().__init__("Update failed")


class NoUpdateAvailableException(Exception):
    def __init__(self):
        super().__init__("No Update available")


class UpdateNotPossibleException(Exception):
    def __init__(self):
        super().__init__("Update not possible")


class BridgeUpdateManager:
    _repo_manager: RepositoryManager
    _current_remote: str
    _current_commit_hash: str
    _current_branch_name: str
    _current_commit_date: str

    def __init__(self, remote: str):
        """
        Initializes the BridgeUpdateManager

        :param remote: The currently configured remote the bridge is running on
        """
        self._current_remote = remote
        self._repo_manager = RepositoryManager(self._current_remote, None)
        try:
            self._current_branch_name = self._repo_manager.get_branch()
            self._repo_manager.init_repository(force_reset=False, reclone_on_error=False)
        except (RepositoryFetchException, RepositoryStatusException):
            raise UpdateNotPossibleException
        self._current_commit_date = self._repo_manager.get_branch_date()
        self._current_commit_hash = self._repo_manager.get_commit_hash()

    def check_for_update(self) -> Union[None, tuple[bool, str, str, str, str, str, str, int]]:
        """
        Checks specified remote for newer version, returns information about remote if newer version exists

        :return: info about the remote, if newer version found, otherwise None
        """
        try:
            self._repo_manager.fetch_from()
        except RepositoryFetchException:
            raise UpdateNotPossibleException
        if self._current_commit_hash == self._repo_manager.get_commit_hash():
            raise NoUpdateAvailableException
        return self._get_update_info(True)

    def _get_update_info(self, update_available: bool) -> tuple[bool, str, str, str, str, str, str, int]:
        return update_available, \
               self._current_commit_hash, \
               self._repo_manager.get_commit_hash(), \
               self._current_branch_name, \
               self._repo_manager.get_branch(), \
               self._current_commit_date, \
               self._repo_manager.get_branch_date(), \
               self._repo_manager.get_num_commits_between_commits()

    def execute_update(self):
        """
        Updates the bridge

        :return: None
        """
        update_successful = self._repo_manager.pull()
        if not update_successful:
            raise UpdateNotSuccessfulException

    @staticmethod
    def reboot():
        """
        Reboots the bridge

        :return: None
        """
        os.system("sys.exit(0)")
