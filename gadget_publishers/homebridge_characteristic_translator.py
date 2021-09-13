from typing import Optional

from smarthome_bridge.characteristic import CharacteristicIdentifier


class CharacteristicParsingError(Exception):
    def __init__(self, characteristic):
        super().__init__(f"Error parsing Characteristic {characteristic}")


class HomebridgeCharacteristicTranslator:

    @staticmethod
    def type_to_string(identifier: CharacteristicIdentifier) -> str:
        """
        Takes a characteristic identifier and returns the fitting string.

        :param identifier: The identifier to parse into a homebridge string
        :return: The string-identifier parsed from the int identifier
        :raises CharacteristicParsingError: If no homebridge string identifier could be founds
        """
        switcher = {
            1: "On",
            2: "RotationSpeed",
            3: "Brightness",
            4: "Hue",
            5: "Saturation"
        }
        res = switcher.get(identifier, None)
        if res is None:
            raise CharacteristicParsingError(identifier)
        return res

    @staticmethod
    def str_to_type(characteristic: str) -> CharacteristicIdentifier:
        """
        Takes a string and returns the fitting characteristic identifier.

        :param characteristic: The homebridge characteristic string to parse
        :return: The parsed characteristic Identifier
        :raises CharacteristicParsingError: If no characteristic identifier for the string could be found
        """
        switcher = {
            "On": CharacteristicIdentifier(1),
            "RotationSpeed": CharacteristicIdentifier(2),
            "Brightness": CharacteristicIdentifier(3),
            "Hue": CharacteristicIdentifier(4),
            "Saturation": CharacteristicIdentifier(5)
        }
        res = switcher.get(characteristic, None)
        if res is None:
            raise CharacteristicParsingError(characteristic)
        return res
