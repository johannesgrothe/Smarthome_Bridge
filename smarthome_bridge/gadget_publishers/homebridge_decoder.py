from logging_interface import LoggingInterface
from smarthome_bridge.gadgets.gadget import Gadget
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator,\
    CharacteristicParsingError


class HomebridgeDecoder(LoggingInterface):

    def __init__(self):
        super().__init__()

    def decode_characteristics(self, json: dict) -> list[Characteristic]:
        """
        Parses the json from homebridge-mqtt into a list of characteristic objects

        :param json: The json to parse
        :return: The list of characteristics parsed
        """
        parsed_json = self._parse_gadget_json(json)
        gadget_characteristics = []
        for characteristic_name in parsed_json:
            try:
                characteristic_ident = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
                min_val = parsed_json[characteristic_name]["minValue"]
                max_val = parsed_json[characteristic_name]["maxValue"]
                steps = (max_val - min_val) // parsed_json[characteristic_name]["minStep"]
                characteristic = Characteristic(characteristic_ident,
                                                min_val,
                                                max_val,
                                                steps)
                gadget_characteristics.append(characteristic)
            except CharacteristicParsingError as err:
                self._logger.error(err.args[0])
        return gadget_characteristics

    @staticmethod
    def _parse_gadget_json(data: dict) -> dict:
        """
        Parses the pure homebridge-mqtt response json into a json containing grouped characteristic information

        :param data: Json to parse
        :return: the parsed json
        """
        characteristic_data = {}
        for service in data["services"]:
            for characteristic in data["services"][service]:
                characteristic_data[characteristic]["value"] = int(data["services"][service][characteristic])
        for service in data["services"]:
            for characteristic in data["services"][service]:
                for key in ["minValue", "maxValue", "minStep"]:
                    characteristic_data[characteristic][key] = data["services"][service][characteristic][key]
        return characteristic_data
