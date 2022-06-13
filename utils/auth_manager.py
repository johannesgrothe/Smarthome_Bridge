from utils.user_manager import UserManager
from system.api_definitions import ApiURIs, ApiAccessLevel


class AuthenticationFailedException(Exception):
    def __init__(self):
        super().__init__("Authentication failed")


class InsufficientAccessPrivilegeException(Exception):
    def __init__(self):
        super().__init__("It saddens us to inform you, but you do not have access to this")


class UnknownUriException(Exception):
    def __init__(self, uri: str):
        super().__init__(f"The URI '{uri}' does not exist in the api definition")


class AuthManager:
    _user_manager: UserManager

    def __init__(self, user_manager: UserManager):
        self._user_manager = user_manager

    @property
    def users(self) -> UserManager:
        return self._user_manager

    def authenticate(self, username: str, password: str):
        """
        Authentication for REST connection
        :param username: Username to check
        :param password: Password to validate
        :return: None
        :raises AuthenticationFailedException: if authentication failed
        :raises UserDoesNotExistException: if user does not exist
        """
        if not self._user_manager.validate_credentials(username, password):
            raise AuthenticationFailedException

    def check_path_access_level_for_user(self, username: str, uri: str):
        """
        Checks whether the user may access this API functionality
        :param username: User that requested access to this functionality
        :param uri: Path of the functionality
        :return: None
        :raises InsufficientAccessPrivilegeException: User, to be checked, doesn't have sufficient access privileges
        :raises UserDoesNotExistException: If user does not exist
        :raises UnknownUriException: Uri requested does not exist in the definitions
        """
        user_access_level = self._user_manager.get_access_level(username)
        return self.check_path_access_level(user_access_level, uri)

    @staticmethod
    def check_path_access_level(access_level: ApiAccessLevel, uri: str):
        """
        Checks whether the user may access this API functionality
        :param access_level: Access_level to check for given path
        :param uri: Path of the functionality
        :return: None
        :raises InsufficientAccessPrivilegeException: Requester, to be checked, doesn't have sufficient access privileges
        :raises UnknownUriException: Uri requested does not exist in the definitions
        """
        try:
            uri_def = ApiURIs.get_definition_for_uri(uri)
            if access_level not in uri_def.access_levels:
                raise InsufficientAccessPrivilegeException
        except ValueError:
            raise UnknownUriException(uri)
