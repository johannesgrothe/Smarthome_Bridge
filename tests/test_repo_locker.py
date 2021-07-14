import pytest
import os
from datetime import datetime, timedelta
from repo_locker import RepoLocker, RepositoryAccessTimeout


@pytest.fixture
def locker():
    locker = RepoLocker(os.getcwd())
    yield locker
    locker.__del__()


def test_repo_locker():
    with RepoLocker(os.getcwd()) as locker:
        assert locker.has_lock()

        start = datetime.now()
        try:
            with RepoLocker(os.getcwd(), 5):
                pass
        except RepositoryAccessTimeout:
            assert start + timedelta(seconds=5) <= datetime.now()
            assert start + timedelta(seconds=5.1) > datetime.now()
            pass
        else:
            assert False
