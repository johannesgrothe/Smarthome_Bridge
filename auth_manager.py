from typing import Optional, Tuple

from user_manager import UserManager


class AuthenticationFailedException(Exception):
    def __init__(self):
        super().__init__("Authentication failed")


class AuthManager:
    _user_manager: UserManager

    def __init__(self):

    def authenticate(self, credentials: Tuple[str, str]):
        """
        Authentication for REST connection
        :param credentials: contains username and password
        :return: True if authentication successful
        :raises AuthenticationFailedException: if authetication failed
        :raises UserDoesNotExistException: if user does not exist
        """
        username, password = credentials
        if not self._user_manager.validate_credentials(username, password):
            raise AuthenticationFailedException

