from typing import Optional

from gadgetlib import CharacteristicIdentifier


class CharacteristicUpdateError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class CharacteristicInitError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Characteristic(object):
    _type: CharacteristicIdentifier
    _min: int
    _max: int
    _steps: int
    _val: int

    def __init__(self, c_type: CharacteristicIdentifier, min_val: int, max_val: int,
                 steps: Optional[int] = None, value: Optional[int] = None):
        """
        :param c_type: Type of the Characteristic
        :param min_val: Minimum true value the characteristic can have (at step value 0)
        :param max_val: Minimum true value the characteristic can have (at step value 'step').
                        Must be bigger than {min_val}
        :param steps: How many steps the value range is divided in. Must be bigger than 0.
                      A value of 4 means it can take 0%, 25%, 50% 75% and 100%
        :param value: The initial step value of the characteristic. Defaults to {min_val}/0
        :raises CharacteristicInitException: If any illegal values are passed
        """
        if min_val >= max_val:
            raise CharacteristicInitError("'min_val' must be bigger than 'max_val'")
        if steps is not None and steps <= 0:
            raise CharacteristicInitError("'steps' must be bigger than 0")
        self._min = min_val
        self._max = max_val
        self._type = c_type

        if steps is not None:
            self._steps = steps
        else:
            self._steps = self._max - self._min

        if value is not None:
            self._val = value
        else:
            self._val = self._min

    def __eq__(self, other):
        """
        Compares another characteristic with this one.
        Does not take into consideration the value of the characteristic.

        :param other: Other object to compare with this one
        :return: Whether the two characteristic is equal with this one
        """
        if isinstance(other, self.__class__):
            return self.get_type() == other.get_type() and \
                   self.get_min() == other.get_min() and \
                   self.get_max() == other.get_max() and \
                   self.get_steps() == other.get_steps()
        return NotImplemented

    def __lt__(self, other) -> bool:
        return self.get_type() < other.get_type()

    def set_step_value(self, value: int) -> bool:
        """
        Sets the step value of a characteristic. Has to be between level 0 and {steps}

        :param value: The step/level the characteristic should be et at
        :return: True if the Update has changed anything, False otherwise
        :raises CharacteristicUpdateError: If an illegal value is passed
        """
        if value < 0 or value > self._steps:
            raise CharacteristicUpdateError(f"Could not set characteristic step: value {value}"
                                            f"is not between {0} and {self._steps}")
        if self._val == value:
            return False
        self._val = value
        return True

    def set_true_value(self, value: int) -> bool:
        """
        Sets the value of the characteristic. Has to be between {min} and {max}.

        Value will be rounded to the closest step, example:
        With min 0, max 100 and 4 steps a value of 55 will be rounded down to 50 / step 3

        :param value: The step/level the characteristic should be et at
        :return: True if the Update has changed anything, False otherwise
        :raises CharacteristicUpdateError: If an illegal value is passed
        """
        if value > self._max or value < self._min:
            raise CharacteristicUpdateError(f"Could not set characteristic: value {value} is"
                                            f"not between {self._min} and {self._max}")

        percentage_value = self._get_percentage_value(value)
        step_value = self._get_step_from_percentage(percentage_value)

        if self._val == step_value:
            return False
        self._val = step_value
        return True

    def _get_percentage_value(self, raw_val: int) -> int:
        return round((raw_val - self._min) / (self._max - self._min) * 100)

    def _get_step_list(self) -> list[int]:
        return [x for x in range(0, 101, 100 // self._steps)]

    def _get_step_from_percentage(self, percentage: int) -> int:
        step_list = self._get_step_list()
        closest_step = self._get_closest(step_list, percentage)
        for index, step in enumerate(step_list):
            if step == closest_step:
                return index

    def _get_true_value_from_percentage(self, percentage: int) -> int:
        return self._min + round((self._max - self._min) / 100 * percentage)

    @staticmethod
    def _get_closest(values: list[int], test_val: int) -> int:
        """
        Returns the element of the list the test_val is closest to

        :param values: Values to search for nearest partner
        :param test_val: Value that should be compared to elements of list
        :return: The element from the list that is closest to test_val
        """
        min_distance = 100
        closest_val = 100
        for val in values:
            distance = max([val - test_val, test_val - val])
            if distance < min_distance:
                min_distance = distance
                closest_val = val
        return closest_val

    def get_true_value(self) -> int:
        """
        :return: The true value of the characteristic between {min} and {max}
        """
        return self._get_true_value_from_percentage(self.get_percentage_value())

    def get_step_value(self) -> int:
        """
        :return: The step value of the characteristic between 0 and {steps}
        """
        return self._val

    def get_percentage_value(self) -> int:
        return self._get_step_list()[self._val]

    def get_type(self) -> CharacteristicIdentifier:
        return self._type

    def get_min(self) -> int:
        return self._min

    def get_max(self) -> int:
        return self._max

    def get_steps(self) -> int:
        return self._steps
