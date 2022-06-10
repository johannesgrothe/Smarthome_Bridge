from lib.logging_interface import ILogging
from system.api_definitions import ApiAccessLevel
import json

import os


class UserAlreadyExistsException(Exception):
    def __init__(self, username: str):
        super().__init__(f"User with username: {username} already exists, please choose another username")


class UserDoesNotExistException(Exception):
    def __init__(self, username: str):
        super().__init__(f"No user with username: {username} found")


class NoPersistentUsersException(Exception):
    def __init__(self):
        super().__init__("Congratz, you somehow managed to brick the with open statement.")


class DeletionNotPossibleException(Exception):
    def __init__(self, username):
        super().__init__(f"User {username}, could not be deleted.")


def _create_user_dict(password: str, access_level: ApiAccessLevel, persistent: bool = False) -> dict:
    """
    Returns a usable dict consisting of user data and credentials

    :param password: Password of the user
    :param access_level: Access level of the user
    :return: Dict containing user info
    """
    return {
        "password": password,
        "access_level": access_level.value,
        "persistent": persistent
    }


class UserManager(ILogging):
    _users: dict
    _persistent_user_path: str

    def __init__(self, data_directory: str):
        super().__init__()
        self._persistent_user_path = os.path.join(data_directory, "persistent_users.json")
        self._users = self._load_persistent_users()

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
        if persistent_user and self.check_if_user_exists(username):
            raise UserAlreadyExistsException(username)

        user = _create_user_dict(password, access_level, persistent_user)
        self._users[username] = user
        self.save_persistent_users()

        p = "Persistent" if persistent_user else "Non persistent"
        self._logger.info(f"{p} user '{username}' added successfully, with access level {str(access_level)}")

    def save_persistent_users(self):
        """
        Saves users with the persistent flag set to true

        :return: None
        """
        save = {"users": []}
        for x, data in self._users.items():
            if data["persistent"]:
                user_meta = {"username": x, "password": data["password"], "access_level": data["access_level"]}
                save["users"].append(user_meta)
        with open(self._persistent_user_path, 'w') as f:
            json.dump(save, f, indent=2)

    def _load_persistent_users(self) -> dict:
        """
        Loads persistent users from persistent_users.json into users dict

        :return: Loaded user data
        """
        load = {}
        try:
            with open(self._persistent_user_path, 'r') as f:
                pers_users = json.load(f)
        except FileNotFoundError:
            return load
        for data in pers_users["users"]:
            info = {"password": data["password"], "access_level": data["access_level"], "persistent": True}
            load[data["username"]] = info
        return load

    def delete_user(self, username: str):
        """
        Deletes a user from the system

        :param username: Username to be deleted
        :return: None
        :raises UserDoesNotExistException: If user does not exist
        :raises DeletionNotPossibleException: If user cannot be deleted
        """
        if username not in self._users:
            raise UserDoesNotExistException(username)
        persistent = self._users[username]["persistent"]
        if not persistent:
            raise DeletionNotPossibleException(username)
        del self._users[username]
        self.save_persistent_users()

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
            raise UserDoesNotExistException(username)
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
            raise UserDoesNotExistException(username)
        return self._users[username]["password"] == password
