from abc import abstractmethod, ABCMeta

from gadgets.gadget import Gadget
from lib.logging_interface import ILogging
from utils.json_validator import Validator


class UpdateApplyError(Exception):
    pass


class GadgetUpdateApplierSuper(ILogging, metaclass=ABCMeta):

    @classmethod
    def apply_update(cls, gadget: Gadget, update_data: dict) -> None:
        """
        Validates the update data and applies it to the passed gadget.

        :param gadget: Gadget to apply the update to
        :param update_data: Dictionary containing the update data
        :return: None
        :raises UpdateApplyError: If anything goes wrong for any reason
        :raises ValidationError: If data is badly formatted
        """
        cls._get_logger().info(f"Applying update to '{gadget.id}'")

        if "name" in update_data:
            gadget.name = update_data["name"]

        attribute_data = update_data["attributes"]
        Validator().validate(attribute_data, cls.get_schema())

        cls.apply_update(gadget, attribute_data)

    @classmethod
    @abstractmethod
    def _apply_update(cls, gadget: Gadget, update_data: dict) -> None:
        """
        Applies update data to the passed gadget. The data is already validated at this point.

        :param gadget: Gadget to apply the update to
        :param update_data: Dictionary containing the update data
        :return: None
        :raises UpdateApplyError: If anything goes wrong for any reason
        """

    @classmethod
    @abstractmethod
    def get_schema(cls) -> str:
        """
        :return: The name of the schema used by this class to validate requests
        """
