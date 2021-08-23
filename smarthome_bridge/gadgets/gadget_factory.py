from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from logging_interface import LoggingInterface

from smarthome_bridge.gadgets.fan_westinghouse_ir import FanWestinghouseIR


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

    def create_gadget(self,
                      gadget_type: GadgetIdentifier,
                      name: str,
                      host_client: str,
                      characteristics: list[Characteristic]) -> Gadget:
        if gadget_type == GadgetIdentifier.fan_westinghouse_ir:
            return self._create_fan_westinghouse_ir(name, host_client, characteristics)
        # elif gadget_type == GadgetIdentifier.lamp_basic:
        #     raise NotImplementedError()
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
