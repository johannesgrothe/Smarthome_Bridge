from typing import Optional, Tuple
from user_manager import UserManager
from system.api_definitions import ApiURIs, ApiAccessLevel, ApiAccessLevelMapping


class AuthenticationFailedException(Exception):
    def __init__(self):
        super().__init__("Authentication failed")


class InsufficientAccessPrivilegeException(Exception):
    def __init__(self):
        super().__init__("It saddens us to inform you, but you do not have access to this")


class AuthManager:
    user_manager: UserManager

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def authenticate(self, credentials: Tuple[str, str]):
        """
        Authentication for REST connection
        :param credentials: contains username and password
        :return: None
        :raises AuthenticationFailedException: if authetication failed
        :raises UserDoesNotExistException: if user does not exist
        """
        username, password = credentials
        if not self.user_manager.validate_credentials(username, password):
            raise AuthenticationFailedException

    def check_path_access_level(self, username: str, uri: ApiURIs):
        """
        Checks whether the user may access this API functionality
        :param username: User that requested access to this functionality
        :param uri: Path of the functionality
        :return: None
        :raises InsufficientAccessPrivilegeException:
        :raises UserDoesNotExistException: if user does not exist
        """
        user_access_level = self.user_manager.get_access_level(username)
        if not uri in ApiAccessLevelMapping.get_mapping(user_access_level):
            raise InsufficientAccessPrivilegeException
