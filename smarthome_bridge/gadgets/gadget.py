"""Module to contain the gadget class"""
from typing import Optional

from smarthome_bridge.characteristic import Characteristic
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier, CharacteristicUpdateStatus


class CharacteristicAlreadyPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is already present")


class CharacteristicNotPresentError(Exception):
    def __init__(self, c_type: int):
        super().__init__(f"Characteristic {c_type} is does not exist in this gadget")


class Gadget:
    _characteristics: [Characteristic]
    _name: str
    _type: GadgetIdentifier
    _host_client: str
    _host_client_runtime_id: int  # TODO: rauskanten

    def __init__(self,
                 name: str,
                 g_type: GadgetIdentifier,
                 host_client: str,
                 host_client_runtime_id: int,
                 characteristics: list[Characteristic]):
        self._name = name
        self._type = g_type
        self._host_client = host_client
        self._host_client_runtime_id = host_client_runtime_id
        self._characteristics = characteristics

    def __del__(self):
        pass
        # while self._characteristics:
        #     characteristic = self._characteristics.pop()
        #     characteristic.__del__()

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

    def add_characteristic(self, characteristic: Characteristic):
        """
        Add a characteristic to a gadget

        :param characteristic: The characteristic to add
        :return: None
        :raises CharacteristicAlreadyPresentError: If characteristic to add already exists in this gadget
        """
        if characteristic.get_type() in [x.get_type() for x in self._characteristics]:
            raise CharacteristicAlreadyPresentError(characteristic.get_type())
        self._characteristics.append(characteristic)

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
