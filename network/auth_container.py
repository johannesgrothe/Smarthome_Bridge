"""Module for all auth containers"""
from abc import ABCMeta


class AuthContainer(metaclass=ABCMeta):
    """Abstract superclass for all other auth containers"""
    pass


class MqttAuthContainer(AuthContainer):
    """Auth container class for pre-verified MQTT"""
    pass


class CredentialsAuthContainer(AuthContainer):
    """Container for authenticating via username and password"""
    username: str
    password: str

    def __init__(self, username: str, password: str):
        """
        Container for authenticating via username and password

        :param username: Username
        :param password: Password
        """
        self.username = username
        self.password = password


class SerialAuthContainer(AuthContainer):
    """Auth container class for pre-verified serial"""
    pass
