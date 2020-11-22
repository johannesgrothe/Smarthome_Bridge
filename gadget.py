"""Module to contain the gadget class"""
from typing import Union, Optional


class Characteristic:

    __name: str
    __min: int
    __max: int
    __step: int
    __val: int

    def __init__(self, name: str, min_val: int, max_val: int, step: int):
        self.__min = min_val
        self.__min = max_val
        self.__step = step
        self.__name = name

    def set_val(self, value: int) -> bool:
        if value > self.__max or value < self.__min:
            return False
        self.__val = value
        return True

    def get_val(self) -> int:
        return self.__val

    def get_name(self) -> str:
        return self.__name


class Gadget:

    __characteristics: [Characteristic]
    __name: str

    def __init__(self, name: str):
        self.__characteristics = []
        self.__name = name

    def __get_characteristic(self, name: str) -> Optional[Characteristic]:
        for characteristic in self.__characteristics:
            if characteristic.get_name() == name:
                return characteristic
        return None

    def add_characteristic(self, name: str, min_val: int, max_val: int, step: int):
        buf_characteristic = Characteristic(name, min_val, max_val, step)
        self.__characteristics.append(buf_characteristic)

    def update_characteristic(self, name: str, value: int) -> bool:
        buf_characteristic = self.__get_characteristic(name)
        if buf_characteristic is None:
            return False
        return buf_characteristic.set_val(value)

    def get_characteristic_value(self, name: str):
        buf_characteristic = self.__get_characteristic(name)
        if buf_characteristic is None:
            return False
        return buf_characteristic.get_val()

    def get_name(self) -> str:
        return self.__name
