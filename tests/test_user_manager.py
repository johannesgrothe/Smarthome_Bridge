import pytest
from utils.user_manager import UserManager, UserDoesNotExistException, DeletionNotPossibleException
from system.api_definitions import ApiAccessLevel

USERNAME1 = "test1"
PW1 = "testpw1"

USERNAME2 = "test3"
PW2 = "testpw2"

ACCESS_LEVEL = ApiAccessLevel.user


@pytest.fixture
def manager(f_temp_exists):
    manager = UserManager(f_temp_exists)
    yield manager
    for user in [USERNAME1, USERNAME2]:
        try:
            manager.delete_user(user)
        except (UserDoesNotExistException, DeletionNotPossibleException):
            pass


def test_add_user(manager: UserManager):
    manager.add_user(username=USERNAME1, password=PW1, access_level=ACCESS_LEVEL, persistent_user=False)
    assert manager.check_if_user_exists(USERNAME1)


def test_add_and_remove_user_persistent(manager: UserManager):
    manager.add_user(username=USERNAME2, password=PW2, access_level=ACCESS_LEVEL, persistent_user=True)
    assert manager.check_if_user_exists(USERNAME2)
    users = manager._load_persistent_users()
    assert USERNAME2 in users

    manager.delete_user(USERNAME2)
    assert not manager.check_if_user_exists(USERNAME2)
    users = manager._load_persistent_users()
    assert USERNAME2 not in users


def test_validate_credentials(manager: UserManager):
    manager.add_user(username=USERNAME2, password=PW2, access_level=ACCESS_LEVEL, persistent_user=False)

    assert manager.validate_credentials(username=USERNAME2, password=PW2)

    with pytest.raises(UserDoesNotExistException):
        manager.validate_credentials(username="blub", password=PW2)

    assert not manager.validate_credentials(username=USERNAME2, password="blub")
