import pytest
from utils.thread_manager import ThreadManager, ThreadIdAlreadyInUseException
import time


_test_flag: bool = False
THREAD_ID = "test_thread"
WRONG_THREAD_ID = "not_existing"


@pytest.fixture
def manager():
    manager = ThreadManager()
    yield manager
    manager.__del__()


def test_method():
    global _test_flag
    _test_flag = True


def test_thread_manager_flag(manager: ThreadManager):
    global _test_flag
    _test_flag = False
    time.sleep(0.1)

    assert _test_flag is False

    manager.add_thread(THREAD_ID, test_method)
    time.sleep(0.1)

    assert _test_flag is False

    manager.start_threads()
    time.sleep(0.1)

    assert _test_flag is True

    manager.remove_thread(THREAD_ID)
    time.sleep(0.1)
    _test_flag = False
    time.sleep(0.1)

    assert _test_flag is False


def test_thread_manager_count(manager: ThreadManager):

    assert manager.get_thread_count() == 0

    manager.add_thread(THREAD_ID, test_method)
    time.sleep(0.1)

    assert manager.get_thread_count() == 1

    manager.remove_thread(THREAD_ID)
    time.sleep(0.1)

    assert manager.get_thread_count() == 0

    manager.add_thread(THREAD_ID, test_method)
    time.sleep(0.1)

    assert manager.get_thread_count() == 1


def test_thread_manager_running(manager: ThreadManager):
    assert manager.get_thread(THREAD_ID) is None

    manager.add_thread(THREAD_ID, test_method)
    time.sleep(0.1)
    saved_thread = manager.get_thread(THREAD_ID)

    assert saved_thread.is_running() is False

    manager.start_threads()

    assert saved_thread.is_running() is True

    manager.__del__()

    assert saved_thread.is_running() is False


def test_thread_manager_add_remove(manager: ThreadManager):

    manager.add_thread(THREAD_ID, test_method)
    time.sleep(0.1)

    assert manager.get_thread_count() == 1

    exception_flag = False
    try:
        manager.add_thread(THREAD_ID, test_method)
    except ThreadIdAlreadyInUseException:
        exception_flag = True
    saved_thread = manager.get_thread(THREAD_ID)

    assert exception_flag is True
    assert manager.get_thread_count() == 1
    assert saved_thread.is_running() is False
    assert saved_thread.get_name() == THREAD_ID

    manager.start_threads()
    exception_flag = False
    try:
        manager.add_thread(THREAD_ID, test_method)
    except ThreadIdAlreadyInUseException:
        exception_flag = True
    saved_thread = manager.get_thread(THREAD_ID)

    assert exception_flag is True
    assert manager.get_thread_count() == 1
    assert saved_thread.is_running() is True

    manager.remove_thread(WRONG_THREAD_ID)

    assert manager.get_thread_count() == 1

    manager.remove_thread(THREAD_ID)

    assert saved_thread.is_running() is False
    assert manager.get_thread_count() == 0
