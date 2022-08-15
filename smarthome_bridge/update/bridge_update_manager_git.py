import datetime
import sys

from smarthome_bridge.update.bridge_update_manager import BridgeUpdateManager, UpdateNotPossibleException, \
    NoUpdateAvailableException, UpdateNotSuccessfulException, BridgeUpdateInformationContainer
from utils.repository_manager import RepositoryManager, RepositoryFetchException, RepositoryStatusException

_default_branch = "master"


class BridgeUpdateManagerGit(BridgeUpdateManager):
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
            raise UpdateNotPossibleException()

    def check_for_update(self) -> BridgeUpdateInformationContainer:
        current_hash = self._repo_manager.get_commit_hash()
        current_date = self._repo_manager.get_branch_date()
        if self._repo_manager.head_is_detached():
            self._logger.info("DETACHED HEAD")
            remote_hash = self._repo_manager.get_commit_hash(_default_branch)
            return BridgeUpdateInformationContainer(current_hash, current_date, remote_hash,
                                                    datetime.datetime.now())

        try:
            self._logger.info("NO DETACHED HEAD")
            self._repo_manager.fetch()
            remote_hash = self._repo_manager.get_commit_hash(self._repo_manager.get_remote_branch())
        except RepositoryFetchException:
            raise UpdateNotPossibleException()
        if current_hash == remote_hash:
            raise NoUpdateAvailableException()
        commits_between = self._repo_manager.get_num_commits_between_commits(current_hash, remote_hash)
        if commits_between == 0:
            raise NoUpdateAvailableException()
        return BridgeUpdateInformationContainer(current_hash, current_date, remote_hash,
                                                datetime.datetime.now())

    def execute_update(self) -> None:
        if self._repo_manager.head_is_detached():
            update_successful = self._repo_manager.checkout(_default_branch)
        else:
            update_successful = self._repo_manager.pull()
        if not update_successful:
            raise UpdateNotSuccessfulException()

    def reboot(self) -> None:
        sys.exit(0)
