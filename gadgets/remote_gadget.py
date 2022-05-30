"""Module to contain the gadget class"""
from typing import Optional, Callable
import logging
from abc import ABCMeta

from gadgets.gadget_event_mapping import GadgetEventMapping
from smarthome_bridge.characteristic import Characteristic
from system.gadget_definitions import CharacteristicIdentifier


class CharacteristicAlreadyPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is already present")


class CharacteristicNotPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is does not exist in this gadget")


class Gadget(metaclass=ABCMeta):
    _characteristics: [Characteristic]
    _name: str
    _logger: logging.Logger
    _event_mapping: list[GadgetEventMapping]

    def __init__(self,
                 name: str,
                 characteristics: list[Characteristic]):
        self._name = name
        self._characteristics = characteristics
        self._characteristics.sort()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._event_mapping = []

    def __del__(self):
        pass

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, self.__class__):
            return self.equals(other) and self.equals_in_characteristics(other)
        return NotImplemented

    def equals(self, other, ignore: Optional[list[Callable]] = None) -> bool:
        if ignore is None:
            ignore = []

        if not isinstance(other, self.__class__):
            return False

        if self.get_name not in ignore:
            if self.get_name() != other.get_name():
                return False

        return True

    def equals_in_characteristics(self, other):
        return self.get_characteristics() == other.get_characteristics()

    def equals_in_characteristic_values(self, other):
        if not self.get_characteristics() == other.get_characteristics():
            return False
        for a, b in zip(self.get_characteristics(), other.get_characteristics()):
            if not a.get_step_value() == b.get_step_value():
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

    def get_characteristics(self) -> list[Characteristic]:
        """
        Returns the gadgets characteristics

        :return: The gadgets characteristics
        """
        return self._characteristics

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

    def get_name(self) -> str:
        return self._name

    def get_characteristic_types(self) -> list[CharacteristicIdentifier]:
        buf_list: [CharacteristicIdentifier] = []
        for characteristic in self._characteristics:
            buf_list.append(characteristic.get_type())
        return buf_list

    def get_event_mapping(self) -> list[GadgetEventMapping]:
        """Returns the configured event mapping of the client"""
        return self._event_mapping

    def set_event_mapping(self, e_mapping: list[GadgetEventMapping]):
        self._event_mapping = e_mapping


class RemoteGadget(Gadget):
    _host_client: str

    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name, characteristics)
        self._host_client = host_client

    def get_host_client(self):
        return self._host_client

    def equals(self, other, ignore: Optional[list[Callable]] = None) -> bool:
        if not super().equals(other, ignore):
            return False

        if self.get_host_client not in ignore:
            if self.get_host_client() != other.get_host_client():
                return False

        return True
