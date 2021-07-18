import pytest
from repository_manager import RepositoryManager, RepositoryCloneException, RepositoryUnsafeToDeleteException,\
    RepositoryCheckoutException, RepositoryFetchException, RepositoryStatusException, RepositoryPullException
import logging


REPO_PATH = "temp"
REPO_NAME = "Smarthome_Infrastructure"
URL = "https://github.com/johannesgrothe/Smarthome_Infrastructure"
REPO_NAME_BROKEN = "Smarthome_Infrastructure_BROKEN"
BROKEN_URL = "https://github.com/johannesgrothe/Smarthome_Infrastructure_BROKEN"
VALID_HASH = "2fee20c56ba4d057a748b472d850959b96ced93b"
INVALID_HASH = "2fee20c56ba4d057a748b472d850959b96ceyolo"
CHECKOUT_BRANCH = "master"


@pytest.fixture
def manager():

    manager = RepositoryManager(REPO_PATH,
                                REPO_NAME,
                                URL)
    yield manager


@pytest.fixture
def manager_broken():

    manager = RepositoryManager(REPO_PATH,
                                REPO_NAME_BROKEN,
                                BROKEN_URL)
    yield manager


@pytest.mark.github_skip
def test_repository_manager(manager: RepositoryManager):
    logging.basicConfig(level="INFO")
    try:
        manager.init_repository(force_reset=True)
    except (RepositoryCloneException, RepositoryUnsafeToDeleteException):
        assert False

    try:
        manager.fetch()
    except RepositoryFetchException:
        assert False

    try:
        manager.checkout(INVALID_HASH)
    except RepositoryCheckoutException:
        pass
    else:
        assert False

    try:
        manager.checkout(VALID_HASH)
    except RepositoryCheckoutException:
        assert False

    assert manager.get_commit_hash() == VALID_HASH

    try:
        manager.pull()
    except RepositoryPullException:
        pass
    else:
        assert False

    try:
        branch = manager.get_branch()
    except RepositoryStatusException:
        assert False
    assert "HEAD" in branch

    try:
        manager.checkout(CHECKOUT_BRANCH)
    except RepositoryCheckoutException:
        assert False
    try:
        branch = manager.get_branch()
    except RepositoryStatusException:
        assert False
    assert branch == CHECKOUT_BRANCH

    try:
        manager.pull()
    except RepositoryPullException:
        assert False

    manager.init_repository(force_reset=False)
    manager.set_safety(True)
    manager.delete_folder()


def test_repository_manager_broken(manager_broken: RepositoryManager):
    try:
        manager_broken.init_repository(force_reset=True)
    except RepositoryCloneException:
        pass
    else:
        assert False
