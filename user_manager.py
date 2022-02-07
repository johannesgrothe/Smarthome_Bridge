from typing import Tuple, Set, List, Dict, Union
from logging_interface import LoggingInterface
from system.api_definitions import ApiAccessLevel, ApiAccessLevelMapping
import json

import os


class UserAlreadyExistsException(Exception):
    def __init__(self, username):
        super().__init__(f"User with username: {username} already exists, please choose another username")


class UserDoesNotExistException(Exception):
    def __init__(self, username):
        super().__init__(f"No user with username: {username} found")


class NoPersistentUsersException(Exception):
    def __init__(self):
        super().__init__("Congratz, you somehow managed to brick the with open statement.")


def _create_user_dict(username: str, password: str, access_level: ApiAccessLevel) \
        -> set[list[dict[str, Union[ApiAccessLevel, str]]]]:
    """
    Returns a usable dict consisting of user data and credentials

    :param username: Name of the user
    :param password: Password of the user
    :param access_level: Access level of the user
    :return: Dict containing user info
    """
    return {
        [
            {
                "username": username,
                "password": password,
                "access_level": access_level
            }
        ]
    }


class UserManager(LoggingInterface):
    _users: dict
    _persistent_user_path: str

    def __init__(self):
        super().__init__()
        self._users = {}
        if not os.path.exists(f"{os.getcwd()}/bridge_data"):
            os.system("mkdir bridge_data")
            self._persistent_user_path = f"{os.getcwd()}/bridge_data/"

    def add_user(self, username: str, password: str, access_level: ApiAccessLevel, persistent_user: bool):
        """
        Adds a user (and credentials) to the system
        :param access_level: ApiAccessLevel of user
        :param username: Username to be added
        :param password: Password to be added (as hash)
        :param persistent_user: Whether the user should be persistent
        :return: None
        :raises UserAlreadyExistsException: if user already exists
        """
        # TODO: add hashing of password
        if self.check_if_user_exists(username):
            raise UserAlreadyExistsException(username)

        if not persistent_user:
            if len(self._users) == 0:
                user = _create_user_dict(username, password, access_level)
                self._users["users"] = user
            else:
                new_user = _create_user_dict(username, password, access_level)
                self._users["users"].append(new_user)
        else:
            pers_user = _create_user_dict(username, password, access_level)
            self._create_persistent_user(pers_user)
            self._logger.info(f"Persistent user {username} was added successfully")
        self._logger.info(f"User {username} added successfully, with access level {access_level.to_string()}")

    def _create_persistent_user(self, users: set[list[dict[str, Union[ApiAccessLevel, str]]]]):
        """
        Adds a persistent user to persistent_users.json file

        :return: None
        """
        if not os.path.exists(self._persistent_user_path):
            os.mkdir("bridge_data")
        for file in os.listdir(self._persistent_user_path):
            file_path = os.path.join(self._persistent_user_path, file)
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                with open(file_name, 'r+') as f:
                    file_data = json.load(f)
                    file_data["users"].append(users)
                    f.seek(0)
                    json.dump(file_data, f, indent=2)
            else:
                with open(f"{self._persistent_user_path}/persistent_users.json", 'x') as f:
                    json.dump(users, f, indent=2)

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

    def get_access_level(self, username: str) -> ApiAccessLevel:
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
