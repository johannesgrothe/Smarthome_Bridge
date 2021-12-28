"""Module for the gadget update information containers"""
from system.gadget_definitions import CharacteristicIdentifier


class CharacteristicUpdateInformation:
    """Container for information to update a gadget with"""

    id: CharacteristicIdentifier
    step_value: int

    def __init__(self, characteristic_id: CharacteristicIdentifier, step_value: int):
        self.id = characteristic_id
        self.step_value = step_value


class GadgetUpdateInformation:
    """Container for information to update a gadget with"""

    id: str
    characteristics: list[CharacteristicUpdateInformation]

    def __init__(self, gadget_id: str, characteristics: list[CharacteristicUpdateInformation]):
        self.id = gadget_id
        self.characteristics = characteristics
