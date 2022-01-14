import os
from typing import Optional, Tuple, Union
from repository_manager import *


class BridgeUpdateManager:
    _repo_manager: RepositoryManager
    _current_remote: str
    _current_commit_hash: str
    _current_branch_name: str
    _current_commit_date: str

    def __init__(self, remote: str):
        self._current_remote = remote
        self._repo_manager = RepositoryManager(self._current_remote, None)
        self._repo_manager.init_repository(force_reset=False)
        self._current_remote = self._repo_manager.fetch_from()
        self._current_commit_hash = self._repo_manager.get_commit_hash()
        self._current_branch_name = self._repo_manager.get_branch()
        self._current_commit_date = self._repo_manager.get_branch_date()

    def check_for_update(self) -> Union[None, tuple[bool, str, str, str, str, str, str, int]]:
        """
        Checks specified remote for newer version, returns information about remote if newer version exists

        :return: info about the remote, if newer version found, otherwise None
        """
        if self._check_for_update():
            return self._get_update_info(self._check_for_update())
        else:
            return None

    def _check_for_update(self) -> bool:
        remote_version = self._repo_manager.fetch_from()
        if remote_version is not self._current_remote:
            return True
        else:
            return False

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

        :return:
        """
        update_successful = self._repo_manager.pull()
        if update_successful:
            os.system("sys.exit(0)")
