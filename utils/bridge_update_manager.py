import sys
from typing import Tuple

from lib.logging_interface import LoggingInterface
from utils.repository_manager import RepositoryManager, RepositoryFetchException, RepositoryStatusException

_default_branch = "master"


class UpdateNotSuccessfulException(Exception):
    def __init__(self):
        super().__init__("Update failed")


class NoUpdateAvailableException(Exception):
    def __init__(self):
        super().__init__("No Update available")


class UpdateNotPossibleException(Exception):
    def __init__(self):
        super().__init__("Update not possible")


class BridgeUpdateManager(LoggingInterface):
    _repo_manager: RepositoryManager
    _bridge_path: str

    def __init__(self, base_path: str):
        """
        Initializes the BridgeUpdateManager

        :param base_path: The path to the bridge software to update
        :raises UpdateNotPossibleException: If no updates can be performed on this bridge instance
        """
        super().__init__()
        self._bridge_path = base_path
        self._logger.info(f"Creating Bridge update manager for bridge at '{self._bridge_path}'")
        self._repo_manager = RepositoryManager(self._bridge_path, None)
        try:
            self._current_branch_name = self._repo_manager.get_branch()
            self._repo_manager.init_repository(force_reset=False, reclone_on_error=False)
        except (RepositoryFetchException, RepositoryStatusException):
            raise UpdateNotPossibleException

    def check_for_update(self) -> Tuple[str, str, str, str, str, int]:
        """
        Checks specified remote for newer version, returns information about remote if newer version exists

        :return: info about the remote, if newer version found, otherwise None
        :raises UpdateNotPossibleException: If no updates can be performed on this bridge instance
        :raises NoUpdateAvailableException: If no updates is available
        """
        current_hash = self._repo_manager.get_commit_hash()
        current_date = self._repo_manager.get_branch_date()
        if self._repo_manager.head_is_detached():
            self._logger.info("DETACHED HEAD")
            remote_hash = self._repo_manager.get_commit_hash(_default_branch)
            return (current_hash,
                    remote_hash,
                    self._repo_manager.get_branch(),
                    current_date,
                    current_date,  # TODO: doesn't work
                    self._repo_manager.get_num_commits_between_commits(current_hash, remote_hash))
        try:
            self._logger.info("NO DETACHED HEAD")
            self._repo_manager.fetch()
            remote_hash = self._repo_manager.get_commit_hash(self._repo_manager.get_remote_branch())
        except RepositoryFetchException:
            raise UpdateNotPossibleException
        if current_hash == remote_hash:
            raise NoUpdateAvailableException
        return (current_hash,
                remote_hash,
                self._repo_manager.get_branch(),
                current_date,
                current_date,  # TODO: doesn't work
                self._repo_manager.get_num_commits_between_commits(current_hash, remote_hash))

    def execute_update(self):
        """
        Updates the bridge

        :return: None
        :raises UpdateNotSuccessfulException: If the updating process failed for any reason
        """
        if self._repo_manager.head_is_detached():
            update_successful = self._repo_manager.checkout(_default_branch)
        else:
            update_successful = self._repo_manager.pull()
        if not update_successful:
            raise UpdateNotSuccessfulException

    @staticmethod
    def reboot():
        """
        Reboots the bridge

        :return: None
        """
        sys.exit(0)
