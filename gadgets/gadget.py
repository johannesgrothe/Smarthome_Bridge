import logging
from abc import ABCMeta, abstractmethod


class IllegalAttributeError(Exception):
    pass


class Gadget(metaclass=ABCMeta):
    _id: str
    _name: str
    _logger: logging.Logger

    __updatable_properties: list[str]

    def __init__(self,
                 gadget_id: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._id = gadget_id
        self._name = self._id
        self.__updatable_properties = []

    def __del__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def _mark_attribute_for_update(self, attribute: str):
        if attribute not in self.__updatable_properties:
            self.__updatable_properties.append(attribute)

    @abstractmethod
    def handle_attribute_update(self, attribute: str, value) -> None:
        """
        Handles update information from an external source

        :param attribute: Attribute to update
        :param value: Value to set the Attribute
        :return: None
        :raises IllegalAttributeError: If attribute does not exist
        :raises ValueError: If value is Illegal
        """

    @abstractmethod
    def access_property(self, property_name: str):
        if property_name == "id":
            return self.id
        elif property_name == "name":
            return self.name
        raise IllegalAttributeError(f"No attribute named '{property_name}' does exist")

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if not self._name == value:
            self._name = value
            self._mark_attribute_for_update("name")

    @property
    def updated_properties(self) -> list[str]:
        return self.__updatable_properties

    def reset_updated_properties(self):
        self.__updatable_properties = []
