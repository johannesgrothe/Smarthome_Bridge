"""Module to contain the gadget class"""
from typing import Optional
from gadgetlib import GadgetIdentifier, CharacteristicIdentifier, CharacteristicUpdateStatus


class Characteristic:
    __type: CharacteristicIdentifier
    __min: int
    __max: int
    __step: int
    __val: int

    def __init__(self, c_type: CharacteristicIdentifier, min_val: int, max_val: int,
                 step: int, value: Optional[int] = None):
        self.__min = min_val
        self.__min = max_val
        self.__step = step
        self.__type = c_type
        if value is not None:
            self.__val = value
        else:
            self.__val = 0

    def set_val(self, value: int) -> CharacteristicUpdateStatus:
        if value > self.__max or value < self.__min:
            return CharacteristicUpdateStatus.update_failed
        if self.__val == value:
            return CharacteristicUpdateStatus.no_update_needed
        self.__val = value
        return CharacteristicUpdateStatus.update_successful

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
    __host_client: str
    __host_client_runtime_id: int

    def __init__(self,
                 name: str,
                 g_type: GadgetIdentifier,
                 host_client: str,
                 host_client_runtime_id: int,
                 characteristics: [Characteristic]):
        self.__name = name
        self.__type = g_type
        self.__host_client = host_client
        self.__host_client_runtime_id = host_client_runtime_id
        self.__characteristics = characteristics

    def update_gadget_info(self,
                           g_type: GadgetIdentifier,
                           host_client: str,
                           host_client_runtime_id: int,
                           new_characteristics: [Characteristic]) -> bool:
        """Updates the information a gadget consists of and returns whether anything important was changed"""
        update_needed = False
        if self.__type != g_type:
            update_needed = True
            self.__type = g_type

        if self.__host_client != host_client:
            # update_needed = True
            self.__host_client = host_client

        if self.__host_client_runtime_id != host_client_runtime_id:
            # update_needed = True
            self.__host_client_runtime_id = host_client_runtime_id

        old_characteristics: [Characteristic] = self.__characteristics
        self.__characteristics = []

        for new_c in new_characteristics:
            found_old_c: Optional[Characteristic] = None
            for old_c in old_characteristics:
                if old_c.get_type() != new_c.get_type():
                    found_old_c = old_c
                    old_characteristics.remove(old_c)

            if found_old_c is not None:
                if found_old_c.get_options() != new_c.get_options():
                    update_needed = True

            self.__characteristics.append(new_c)

        if old_characteristics:
            update_needed = True

        return update_needed

    def __get_characteristic(self, c_type: CharacteristicIdentifier) -> Optional[Characteristic]:
        for characteristic in self.__characteristics:
            if characteristic.get_type() == c_type:
                return characteristic
        return None

    def add_characteristic(self, c_type: CharacteristicIdentifier, min_val: int, max_val: int, step: int):
        buf_characteristic = Characteristic(c_type, min_val, max_val, step)
        self.__characteristics.append(buf_characteristic)

    def update_characteristic(self, c_type: CharacteristicIdentifier, value: int) -> CharacteristicUpdateStatus:
        buf_characteristic = self.__get_characteristic(c_type)
        if buf_characteristic is None:
            return CharacteristicUpdateStatus.unknown_characteristic
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

    def get_host_client(self):
        return self.__host_client

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
