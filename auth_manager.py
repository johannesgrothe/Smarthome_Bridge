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

    def authenticate(self, username: str, password: str):
        """
        Authentication for REST connection
        :param username: Username to check
        :param password: Password to validate
        :return: None
        :raises AuthenticationFailedException: if authentication failed
        :raises UserDoesNotExistException: if user does not exist
        """
        if not self.user_manager.validate_credentials(username, password):
            raise AuthenticationFailedException

    def check_path_access_level_for_user(self, username: str, uri: ApiURIs):
        """
        Checks whether the user may access this API functionality
        :param username: User that requested access to this functionality
        :param uri: Path of the functionality
        :return: None
        :raises InsufficientAccessPrivilegeException: user, to be checked, doesn't have sufficient access privileges
        :raises UserDoesNotExistException: if user does not exist
        """
        user_access_level = self.user_manager.get_access_level(username)
        return self.check_path_access_level(user_access_level, uri)

    @staticmethod
    def check_path_access_level(access_level: ApiAccessLevel, uri: ApiURIs):
        """
        Checks whether the user may access this API functionality
        :param access_level: access_level to check for given path
        :param uri: Path of the functionality
        :return: None
        :raises InsufficientAccessPrivilegeException: requester, to be checked, doesn't have sufficient access privileges
        """
        if uri not in ApiAccessLevelMapping.get_mapping(access_level):
            raise InsufficientAccessPrivilegeException
