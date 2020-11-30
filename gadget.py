"""Module to contain the gadget class"""
from typing import Union, Optional
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier


class Characteristic:
    __type: CharacteristicIdentifier
    __min: int
    __max: int
    __step: int
    __val: int

    def __init__(self, c_type: CharacteristicIdentifier, min_val: int, max_val: int, step: int):
        self.__min = min_val
        self.__min = max_val
        self.__step = step
        self.__type = c_type

    def set_val(self, value: int) -> bool:
        if value > self.__max or value < self.__min:
            return False
        self.__val = value
        return True

    def get_val(self) -> int:
        return self.__val

    def get_type(self) -> CharacteristicIdentifier:
        return self.__type

    def get_options(self) -> (int, int, int):
        return self.__min, self.__max, self.__step

    def get_json_representation(self) -> dict:
        return {"type": int(self.__type), "min": self.__min, "max": self.__max, "step": self.__step,
                "value": self.__val}


class Gadget:
    __characteristics: [Characteristic]
    __name: str
    __type: GadgetIdentifier

    def __init__(self, name: str, g_type: GadgetIdentifier):
        self.__characteristics = []
        self.__name = name
        self.__type = g_type

    def __get_characteristic(self, c_type: CharacteristicIdentifier) -> Optional[Characteristic]:
        for characteristic in self.__characteristics:
            if characteristic.get_type() == c_type:
                return characteristic
        return None

    def add_characteristic(self, c_type: CharacteristicIdentifier, min_val: int, max_val: int, step: int):
        buf_characteristic = Characteristic(c_type, min_val, max_val, step)
        self.__characteristics.append(buf_characteristic)

    def update_characteristic(self, c_type: CharacteristicIdentifier, value: int) -> bool:
        buf_characteristic = self.__get_characteristic(c_type)
        if buf_characteristic is None:
            return False
        return buf_characteristic.set_val(value)

    def get_characteristic_value(self, c_type: CharacteristicIdentifier):
        buf_characteristic = self.__get_characteristic(c_type)
        if buf_characteristic is None:
            return False
        return buf_characteristic.get_val()

    def get_characteristic_options(self, c_type: CharacteristicIdentifier) -> (int, int, int):
        buf_characteristic = self.__get_characteristic(c_type)
        if buf_characteristic is None:
            return None, None, None
        return buf_characteristic.get_options()

    def get_name(self) -> str:
        return self.__name

    def get_type(self) -> GadgetIdentifier:
        return self.__type

    def get_characteristic_types(self) -> [CharacteristicIdentifier]:
        buf_list: [CharacteristicIdentifier] = []
        for characteristic in self.__characteristics:
            buf_list.append(characteristic.get_type())
        return buf_list

    def get_json_representation(self) -> dict:
        buf_json = {"type": int(self.__type), "name": self.__name, "characteristics": []}
        for characteristic in self.__characteristics:
            buf_json["characteristics"].append(characteristic.get_json_representation())
        return buf_json
