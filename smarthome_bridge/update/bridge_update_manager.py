import datetime
from abc import abstractmethod, ABCMeta
from typing import Tuple

from lib.logging_interface import ILogging


class UpdateNotSuccessfulException(Exception):
    def __init__(self):
        super().__init__("Update failed")


class NoUpdateAvailableException(Exception):
    def __init__(self):
        super().__init__("No Update available")


class UpdateNotPossibleException(Exception):
    def __init__(self):
        super().__init__("Update not possible")


class BridgeUpdateInformationContainer:
    current_version: str
    current_date: datetime.datetime
    new_version: str
    new_date: datetime.datetime

    def __init__(self,
                 current_version: str,
                 current_date: datetime.datetime,
                 new_version: str,
                 new_date: datetime.datetime):
        self.current_version = current_version
        self.current_date = current_date
        self.new_version = new_version
        self.new_date = new_date


class BridgeUpdateManager(ILogging, metaclass=ABCMeta):

    def __init__(self):
        """
        Initializes the BridgeUpdateManager

        :param base_path: The path to the bridge software to update
        :raises UpdateNotPossibleException: If no updates can be performed on this bridge instance
        """
        super().__init__()

    @abstractmethod
    def check_for_update(self) -> BridgeUpdateInformationContainer:
        """
        Checks specified remote for newer version, returns information about remote if newer version exists

        :return: info about the remote, if newer version found, otherwise None
        :raises UpdateNotPossibleException: If no updates can be performed on this bridge instance
        :raises NoUpdateAvailableException: If no updates is available
        """

    @abstractmethod
    def execute_update(self) -> None:
        """
        Updates the bridge

        :return: None
        :raises UpdateNotSuccessfulException: If the updating process failed for any reason
        """

    @abstractmethod
    def reboot(self) -> None:
        """
        Reboots the bridge

        :return: None
        """
