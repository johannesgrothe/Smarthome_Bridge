"""Module to contain the gadget class"""
from typing import Optional
import logging
from abc import ABCMeta, abstractmethod

from smarthome_bridge.characteristic import Characteristic
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier, CharacteristicUpdateStatus


class CharacteristicAlreadyPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is already present")


class CharacteristicNotPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is does not exist in this gadget")


class Gadget(object, metaclass=ABCMeta):
    _characteristics: [Characteristic]
    _name: str
    _type: GadgetIdentifier
    _host_client: str
    _logger: logging.Logger

    def __init__(self,
                 name: str,
                 g_type: GadgetIdentifier,
                 host_client: str,
                 characteristics: list[Characteristic]):
        self._name = name
        self._type = g_type
        self._host_client = host_client
        self._characteristics = characteristics
        self._logger = logging.getLogger(self.__class__.__name__)

    def __del__(self):
        pass
        # while self._characteristics:
        #     characteristic = self._characteristics.pop()
        #     characteristic.__del__()

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, self.__class__):
            return self.get_name() == other.get_name() and\
                   self.get_type() == other.get_type() and\
                   self.get_host_client() == other.get_host_client() and\
                   self._characteristics_are_equal(other)
        return NotImplemented

    def _characteristics_are_equal(self, other) -> bool:
        """
        Compares the characteristics of this gadget with the characteristics of another one

        :param other: Gadget to compare characteristics with
        :return: Whether the characteristics are equal
        """
        if not len(self.get_characteristic_types()) == len(other.get_characteristic_types()):
            return False
        for c_type in self.get_characteristic_types():
            if self.get_characteristic(c_type) is None or other.get_characteristic(c_type) is None:
                return False
            if not self.get_characteristic(c_type) == other.get_characteristic(c_type):
                return False
        return True

    def get_characteristic(self, c_type: CharacteristicIdentifier) -> Optional[Characteristic]:
        """
        Returns the characteristic fitting the given identifier if possible

        :param c_type: The characteristic identifier to search for
        :return: The characteristic fitting the given identifier if possible
        """
        for characteristic in self._characteristics:
            if characteristic.get_type() == c_type:
                return characteristic
        return None

    def update_characteristic(self, c_type: CharacteristicIdentifier, step_value: int) -> bool:
        """
        Updates a characteristic with the given step value

        :param c_type: The identifier of the characteristic to change
        :param step_value: The step value the characteristic should get
        :return: True if the update changed anything, False if not.
        :raises CharacteristicNotPresentError: If no characteristic with the given identifier could be found
        """
        buf_characteristic = self.get_characteristic(c_type)
        if buf_characteristic is None:
            raise CharacteristicNotPresentError(c_type)
        return buf_characteristic.set_step_value(step_value)

    def get_characteristic_step_value(self, c_type: CharacteristicIdentifier):
        buf_characteristic = self.get_characteristic(c_type)
        if buf_characteristic is None:
            raise CharacteristicNotPresentError(c_type)
        return buf_characteristic.get_step_value()

    def get_characteristic_options(self, c_type: CharacteristicIdentifier) -> (int, int, int):
        buf_characteristic = self.get_characteristic(c_type)
        if buf_characteristic is None:
            raise CharacteristicNotPresentError(c_type)
        return buf_characteristic.get_min(), buf_characteristic.get_max(), buf_characteristic.get_steps()

    def get_host_client(self):
        return self._host_client

    def get_name(self) -> str:
        return self._name

    def get_type(self) -> GadgetIdentifier:
        return self._type

    def get_characteristic_types(self) -> [CharacteristicIdentifier]:
        buf_list: [CharacteristicIdentifier] = []
        for characteristic in self._characteristics:
            buf_list.append(characteristic.get_type())
        return buf_list
