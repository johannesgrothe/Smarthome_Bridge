from typing import Optional
import os
from datetime import datetime, timedelta


_repo_lockfile_path = "repo.lock"


class RepositoryAccessTimeout(Exception):
    def __init__(self, timeout: int):
        super().__init__(f"Repository could not be accessed: Timeout of {timeout} seconds has passed")


class RepoLocker:

    _max_delay: Optional[int]
    _has_repo_locked: bool
    _repo_path: str

    def __init__(self, repo_path: str, max_delay: Optional[int] = None):
        self._repo_path = repo_path
        self._max_delay = max_delay
        self._has_repo_locked = False

    def __del__(self):
        self._release_repository_lock()

    def __enter__(self):
        self.lock_repository()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._release_repository_lock()

    def has_lock(self):
        return self._has_repo_locked

    def _write_repository_lock(self):
        if not self._has_repo_locked:
            with open(os.path.join(self._repo_path, _repo_lockfile_path), 'w') as f:
                f.write('This is a lock file created by the chip flasher.\n'
                        'If you have any problems with the chip flasher module, '
                        'shut down all sunning instances and delete this file.')
            self._has_repo_locked = True

    def _release_repository_lock(self):
        if self._has_repo_locked:
            self._has_repo_locked = False
            os.remove(os.path.join(self._repo_path, _repo_lockfile_path))

    def _wait_for_repository(self):
        """Waits for the cloned repository to be available (not used by any other process)"""
        start_time = datetime.now()
        while os.path.isfile(os.path.join(self._repo_path, _repo_lockfile_path)):
            if self._max_delay is not None:
                if start_time + timedelta(seconds=self._max_delay) < datetime.now():
                    raise RepositoryAccessTimeout(self._max_delay)

    def lock_repository(self):
        self._wait_for_repository()
        self._write_repository_lock()
