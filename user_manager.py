from typing import Tuple
from logging_interface import LoggingInterface
from system.api_definitions import ApiAccessLevel, ApiAccessLevelMapping


class UserAlreadyExistsException(Exception):
    def __init__(self, username):
        super().__init__(f"User with username: {username} already exists, please choose another username")


class UserDoesNotExistException(Exception):
    def __init__(self, username):
        super().__init__(f"No user with username: {username} found")


class UserManager(LoggingInterface):
    _users: dict

    def __init__(self):
        super().__init__()
        self._users = {}

    def add_user(self, username: str, password: str, access_level: ApiAccessLevel):
        """
        Adds a user (and credentials) to the system
        :param access_level: ApiAccessLevel of user
        :param username: Username to be added
        :param password: Password to be added (as hash)
        :return: None
        :raises UserAlreadyExistsException: if user already exists
        """
        # TODO: add hashing of password with method from flask library
        if self.check_if_user_exists(username):
            raise UserAlreadyExistsException(username)

        self._users[username] = {
            "pw": password,
            "access_level": access_level
        }
        self._logger.info(f"User {username} added successfully, with access level {access_level.to_string()}")

    def delete_user(self, username: str):
        """
        Deletes a user from the system
        :param username: Username to be deleted
        :return: None
        """
        # TODO: delete user and credentials

    def check_if_user_exists(self, username: str) -> bool:
        """
        Checks whether the specified user already exists
        :param username: Username to be checked
        :return: Whether user already exists or not
        """
        if username in self._users:
            return True
        return False

    def get_access_level(self, username:str) -> ApiAccessLevel:
        if not self.check_if_user_exists(username):
            raise UserDoesNotExistException
        return self._users[username]["access_level"]

    def validate_credentials(self, username: str, password: str) -> bool:
        """
        Checks if given password is valid, for given username
        :param username: Username to check
        :param password: Password to validate
        :return: True, if password is valid
        :raises UserDoesNotExistException: if user does not exist
        """
        if not self.check_if_user_exists(username):
            raise UserDoesNotExistException
        return self._users[username] == password
