import pytest

from test_helpers.runtime_test_manager import RuntimeTestManager


@pytest.fixture
def manager():
    manager = RuntimeTestManager()
    yield manager


@pytest.mark.github_skip
def test_runtime_test_manager(manager: RuntimeTestManager):
    manager.add_task(0, print, ["test0 (Every Second)"])
    manager.add_task(1, print, ["test1 (Every 2 Seconds)"])
    manager.add_task(2, print, ["test2 (Every 4 Seconds)"])
    manager.run(10)
