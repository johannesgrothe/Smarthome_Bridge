from gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from logging_interface import LoggingInterface

from gadgets.any_gadget import AnyGadget
from gadgets.fan_westinghouse_ir import FanWestinghouseIR
from gadgets.lamp_neopixel_basic import LampNeopixelBasic


class CharacteristicNotFoundError(Exception):
    def __init__(self, characteristic: CharacteristicIdentifier):
        super().__init__(f"Unable to find characteristic '{characteristic}'")


class GadgetCreationError(Exception):
    def __init__(self, name: str, g_type: GadgetIdentifier):
        super().__init__(f"Unable to create gadget '{name}' of type '{g_type}'")


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

    @staticmethod
    def merge_gadgets(old_gadget: Gadget, new_gadget: Gadget) -> Gadget:
        factory = GadgetFactory()
        merged_gadget = factory.create_gadget(old_gadget.get_type(),
                                              old_gadget.get_name(),
                                              old_gadget.get_host_client(),
                                              new_gadget.get_characteristics())
        return merged_gadget

    @staticmethod
    def create_any_gadget(name: str,
                          host_client: str,
                          characteristics: list[Characteristic]) -> AnyGadget:
        return AnyGadget(name,
                         host_client,
                         characteristics)

    def create_gadget(self,
                      gadget_type: GadgetIdentifier,
                      name: str,
                      host_client: str,
                      characteristics: list[Characteristic]) -> Gadget:
        if gadget_type == GadgetIdentifier.fan_westinghouse_ir:
            return self._create_fan_westinghouse_ir(name, host_client, characteristics)
        elif gadget_type == GadgetIdentifier.lamp_neopixel_basic:
            return self._create_lamp_neopixel_basic(name, host_client, characteristics)
        else:
            raise NotImplementedError()

    def _create_fan_westinghouse_ir(self,
                                    name: str,
                                    host_client: str,
                                    characteristics: list[Characteristic]) -> FanWestinghouseIR:
        try:
            status = self._get_characteristic_from_list(CharacteristicIdentifier.status, characteristics)
            fan_speed = self._get_characteristic_from_list(CharacteristicIdentifier.fanSpeed, characteristics)
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
            lamp = LampNeopixelBasic(name,
                                     host_client,
                                     status,
                                     brightness,
                                     hue)
            return lamp
        except CharacteristicNotFoundError as err:
            self._logger.error(err.args[0])
            raise GadgetCreationError(name, GadgetIdentifier.lamp_neopixel_basic)
