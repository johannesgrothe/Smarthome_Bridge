import pytest
from user_manager import UserManager
from system.api_definitions import ApiAccessLevel

USERNAME1 = "test1"
PW1 = "testpw1"

USERNAME2 = "test3"
PW2 = "testpw2"

ACCESS_LEVEL = ApiAccessLevel.user


@pytest.fixture
def manager():
    manager = UserManager()
    yield manager


def test_add_user(manager: UserManager):
    manager.add_user(username=USERNAME1, password=PW1, access_level=ACCESS_LEVEL, persistent_user=False)
    assert manager.check_if_user_exists(USERNAME1)


def test_add_user_persistent(manager: UserManager):
    manager.add_user(username=USERNAME2, password=PW2, access_level=ACCESS_LEVEL, persistent_user=True)
    users = manager._load_persistent_users()
    assert USERNAME2 in users


def test_validate_credentials(manager: UserManager):
    manager.validate_credentials(username=USERNAME2, password=PW2)


def test_delete_user(manager: UserManager):
    manager.delete_user(USERNAME2)
    assert not manager.check_if_user_exists(USERNAME2)
