from gadgets.gadget import Gadget
from system.gadget_definitions import GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from logging_interface import LoggingInterface

from gadgets.any_gadget import AnyGadget
from gadgets.fan_westinghouse_ir import FanWestinghouseIR
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from smarthome_bridge.api_encoder import ApiEncoder, IdentifierEncodeError


class CharacteristicNotFoundError(Exception):
    def __init__(self, characteristic: CharacteristicIdentifier):
        super().__init__(f"Unable to find characteristic '{characteristic}'")


class GadgetCreationError(Exception):
    def __init__(self, name: str, g_type: GadgetIdentifier):
        super().__init__(f"Unable to create gadget '{name}' of type '{g_type}'")


class GadgetMergeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class GadgetFactory(LoggingInterface):

    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_characteristic_from_list(ident: CharacteristicIdentifier, data: list[Characteristic]):
        """
        Finds a characteristic in a list

        :param ident: Characteristic to find
        :param data: List to get characteristic from
        :return: The found characteristic
        :raises CharacteristicNotFoundError: If characteristic could not be found
        """
        for characteristic in data:
            if characteristic.get_type() == ident:
                return characteristic
        raise CharacteristicNotFoundError(ident)

    def merge_gadgets(self, old_gadget: Gadget, new_gadget: Gadget) -> Gadget:
        """
        Merges two gadgets (typically one 'original' and a new one with update information) into a new gadget
        containing with name, client and class of the old and characteristics of the new one.

        :param old_gadget: Original gadget to base merged gadget on
        :param new_gadget: Gadget wth update information
        :return: The emrged gadget
        :raise GadgetMergeError: If anything goes wrong during merges
        """
        encoder = ApiEncoder()
        if not isinstance(new_gadget, AnyGadget) and old_gadget.__class__ != new_gadget.__class__:
            raise GadgetMergeError(f"Cannot merge gadgets with different classes {old_gadget.__class__.__name__} "
                                   f"and {new_gadget.__class__.__name__}")
        try:
            gadget_type = encoder.encode_gadget_identifier(old_gadget)
        except IdentifierEncodeError as err:
            raise GadgetMergeError(err.args[0])
        try:
            merged_gadget = self.create_gadget(gadget_type,
                                               old_gadget.get_name(),
                                               old_gadget.get_host_client(),
                                               new_gadget.get_characteristics())
        except GadgetCreationError as err:
            raise GadgetMergeError(err.args[0])
        return merged_gadget

    @staticmethod
    def create_any_gadget(name: str,
                          host_client: str,
                          characteristics: list[Characteristic]) -> AnyGadget:
        """
        Creates a new 'AnyGadget' from the passed data

        :param name: Name for the newly created gadget
        :param host_client: Host-Client for the newly created gadget
        :param characteristics: Characteristics for the newly created gadget
        :return: The newly created gadget
        """
        return AnyGadget(name,
                         host_client,
                         characteristics)

    def create_gadget(self,
                      gadget_type: GadgetIdentifier,
                      name: str,
                      host_client: str,
                      characteristics: list[Characteristic]) -> Gadget:
        """
        Creates a new Gadget from the passed data

        :param gadget_type: Type to infer the class for the new gadget from
        :param name: Name for the newly created gadget
        :param host_client: Host-Client for the newly created gadget
        :param characteristics: Characteristics for the newly created gadget
        :return: The newly created gadget
        """
        if gadget_type == GadgetIdentifier.fan_westinghouse_ir:
            return self._create_fan_westinghouse_ir(name, host_client, characteristics)
        elif gadget_type == GadgetIdentifier.lamp_neopixel_rgb_basic:
            return self._create_lamp_neopixel_basic(name, host_client, characteristics)
        else:
            raise NotImplementedError()

    def _create_fan_westinghouse_ir(self,
                                    name: str,
                                    host_client: str,
                                    characteristics: list[Characteristic]) -> FanWestinghouseIR:
        try:
            status = self._get_characteristic_from_list(CharacteristicIdentifier.status, characteristics)
            fan_speed = self._get_characteristic_from_list(CharacteristicIdentifier.fan_speed, characteristics)
            fan = FanWestinghouseIR(name,
                                    host_client,
                                    status,
                                    fan_speed)
            return fan
        except CharacteristicNotFoundError as err:
            self._logger.error(err.args[0])
            raise GadgetCreationError(name, GadgetIdentifier.fan_westinghouse_ir)

    def _create_lamp_neopixel_basic(self,
                                    name: str,
                                    host_client: str,
                                    characteristics: list[Characteristic]) -> LampNeopixelBasic:
        try:
            status = self._get_characteristic_from_list(CharacteristicIdentifier.status, characteristics)
            brightness = self._get_characteristic_from_list(CharacteristicIdentifier.brightness, characteristics)
            hue = self._get_characteristic_from_list(CharacteristicIdentifier.hue, characteristics)
            saturation = self._get_characteristic_from_list(CharacteristicIdentifier.saturation, characteristics)
            lamp = LampNeopixelBasic(name,
                                     host_client,
                                     status,
                                     brightness,
                                     hue,
                                     saturation)
            return lamp
        except CharacteristicNotFoundError as err:
            self._logger.error(err.args[0])
            raise GadgetCreationError(name, GadgetIdentifier.lamp_neopixel_rgb_basic)
