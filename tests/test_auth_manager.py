import pytest
from auth_manager import AuthManager, AuthenticationFailedException, InsufficientAccessPrivilegeException
from user_manager import UserManager, ApiAccessLevel
from system.api_definitions import ApiURIs


@pytest.fixture
def manager_user():
    manager = UserManager()
    manager.add_user("test2", "testpw2", ApiAccessLevel.user, True)
    yield manager
    manager.delete_user("test2")


@pytest.fixture
def manager(manager_user: UserManager):
    manager = AuthManager(manager_user)
    yield manager


def test_authenticate(manager: AuthManager):
    try:
        manager.authenticate(username="test2", password="testpw2")
    except AuthenticationFailedException:
        assert False


def test_check_path_access_level_for_user(manager: AuthManager):
    try:
        manager.check_path_access_level_for_user("test2", ApiURIs.info_bridge.uri)
    except InsufficientAccessPrivilegeException:
        assert False
