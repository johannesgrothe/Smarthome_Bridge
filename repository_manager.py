"""Module to contain the RepositoryManager and its Exceptions"""
import os
import logging
from typing import Optional


class RepositoryUnsafeToDeleteException(Exception):
    def __init__(self, path):
        super().__init__(f"The selected directory is no valid git repository: '{path}'")


class RepositoryStatusException(Exception):
    def __init__(self):
        super().__init__(f"General repository error")


class RepositoryCloneException(Exception):
    def __init__(self):
        super().__init__(f"Cloning repository failed.")


class RepositoryFetchException(Exception):
    def __init__(self):
        super().__init__(f"Fetching repository failed.")


class RepositoryCheckoutException(Exception):
    def __init__(self, branch: str):
        super().__init__(f"Failed to check out '{branch}'.")


class RepositoryPullException(Exception):
    def __init__(self):
        super().__init__(f"Pulling repository failed.")


class RepositoryManager:
    """
    Class that allows for management of a git repository
    """
    _path: str
    _base_path: str
    _repo_name: str
    _remote_url: Optional[str]
    _logger: logging.Logger
    _safe_mode: bool

    def __init__(self, base_path: str, repository_name: str, remote_url: Optional[str] = None):
        """
        Constructor for the RepositoryManager Class
        :param base_path: Path the repository folder exists or should be created in
        :param repository_name: The name of the folder the repository exists or should be created in
        :param remote_url: The remote url the repository should be cloned from if needed
        """
        self._safe_mode = False
        self._base_path = os.path.abspath(base_path)
        self._repo_name = repository_name
        self._path = os.path.join(self._base_path, self._repo_name)
        self._remote_url = remote_url
        self._logger = logging.getLogger("RepositoryManager")

    def _exec_git_command(self, command: str) -> bool:
        """
        Executes the selected command at the repository folder.
        :param command: The command to execute
        :return: True if return code of command is 0
        """
        return os.system(f"cd {self._path};{command}") == 0

    def _dir_is_safe_to_delete(self) -> bool:
        """
        Checks if the directory is safe to delete.
        :return: True if repo is safe to delete or safe mode is deactivated
        """
        if not self._safe_mode:
            return True
        current_workdir = os.path.abspath(os.getcwd())
        repo_is_inside_workdir = self._path.startswith(current_workdir)
        return repo_is_inside_workdir

    def set_safety(self, safe_mode: bool):
        """
        By default, the manager can only delete repositories inside of its parent scripts working directory.\n
        Setting this to 'False' allows the Manager to delete Folders everywhere on the disk.\n
        Beware you could delete your whole hard disk by messing this up.
        """
        self._safe_mode = safe_mode

    def delete_folder(self):
        """
        Deletes the folder containing the repository if it's safe to do so.
        :raises RepositoryUnsafeToDeleteException: When the repository folder is not safe to delete
        """
        if not self._dir_is_safe_to_delete():
            raise RepositoryUnsafeToDeleteException

        for root, dirs, files in os.walk(self._path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def init_repository(self, force_reset: bool):
        """
        Checks if the repository exists and works. Clones the repository if it does not exist at the given path.
        :param force_reset: Whether repository should be deleted and re-clone
        :raises RepositoryCloneException: When cloning the repository fails
        """
        repo_works = False

        if force_reset:
            if os.path.isdir(self._path):
                self.delete_folder()
        else:
            if os.path.isdir(self._path):
                repo_clean = os.system(f"cd {self._path};git diff --quiet") == 0
                repo_works = repo_clean

        if not repo_works:
            self._logger.info(f"Repo doesn't exist or is broken, deleting dir"
                              f"and cloning repository from '{self._remote_url}'")
            if os.path.isdir(self._path):
                self.delete_folder()

            repo_works = os.system(f"cd {self._base_path};git clone {self._remote_url} {self._repo_name} --quiet") == 0

        if not repo_works:
            self._logger.error(f"Error cloning repository from '{self._remote_url}'")
            raise RepositoryCloneException

    def fetch(self):
        """
        Fetches from all configured remotes.
        :raises RepositoryFetchException: When fetching from remotes fails for any reason
        """
        self._logger.info(f"Fetching from all remotes...")
        fetch_ok = self._exec_git_command("git fetch --all --quiet")
        if not fetch_ok:
            self._logger.error("Fetching repository failed.")
            raise RepositoryFetchException
        else:
            self._logger.info("Fetching repository was successful.")

    def checkout(self, branch: str):
        """
        Checks out the selected branch.
        :param branch: Branch to check out
        :raises RepositoryFetchException: When checking out branch fails for any reason
        """
        self._logger.info(f"Checking out '{branch}'...")
        checkout_successful = self._exec_git_command(f"git checkout {branch} --quiet")
        if not checkout_successful:
            self._logger.error(f"Failed to check out '{branch}'.")
            raise RepositoryCheckoutException(branch)
        self._logger.info(f"Checking out '{branch}' was successful.")

    def pull(self):
        """
        Pulls the configured remote branch into current one
        :raises RepositoryFetchException: When pulling fails for any reason
        """
        pull_ok = self._exec_git_command("git pull --quiet")
        if not pull_ok:
            self._logger.error("Failed to pull from remote repository")
            raise RepositoryPullException
        self._logger.info("Pulling from remote repository was successful")

    def get_commit_hash(self) -> str:
        """
        Gets the current git commit hash.
        :return: The current commit hash
        """
        return os.popen(f"cd {self._path};git rev-parse HEAD").read().strip("\n")

    def get_branch(self) -> str:
        """
        Gets the current git branch.
        :return: The current git branch.
        """
        branch_list = [x.strip().strip("*").strip()
                       for x
                       in os.popen(f"cd {self._path};git branch").read().strip("\n").split("\n")
                       if x.strip().startswith("*")]
        if len(branch_list) != 1:
            raise RepositoryStatusException
        return branch_list[0]
