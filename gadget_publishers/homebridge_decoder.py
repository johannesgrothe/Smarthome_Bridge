from lib.logging_interface import LoggingInterface
from smarthome_bridge.characteristic import Characteristic
from gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator, \
    CharacteristicParsingError


class HomebridgeDecoder(LoggingInterface):

    def __init__(self):
        super().__init__()

    def decode_characteristics(self, json: dict) -> list[Characteristic]:
        """
        Parses the json from homebridge-mqtt into a list of characteristic objects

        :param json: The json to parse
        :return: A list with the characteristics parsed from the json
        """
        parsed_json = self._parse_gadget_json(json)
        gadget_characteristics = []
        for characteristic_name in parsed_json:
            try:
                characteristic_ident = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
                min_val = parsed_json[characteristic_name]["minValue"]
                max_val = parsed_json[characteristic_name]["maxValue"]
                steps = (max_val - min_val) // parsed_json[characteristic_name]["minStep"]
                current_val = parsed_json[characteristic_name]["value"]
                characteristic = Characteristic(characteristic_ident,
                                                min_val,
                                                max_val,
                                                steps)
                characteristic.set_true_value(current_val)
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
        for service in data["characteristics"]:
            for characteristic in data["characteristics"][service]:
                characteristic_data[characteristic] = {}
                try:
                    value = int(data["characteristics"][service][characteristic])
                except ValueError:
                    value = None
                characteristic_data[characteristic]["value"] = value
        for service in data["properties"]:
            for characteristic in data["properties"][service]:
                for key in ["minValue", "maxValue", "minStep"]:
                    if data["properties"][service][characteristic]["format"] == "bool":
                        value_map = {
                            "minValue": 0,
                            "maxValue": 1,
                            "minStep": 1
                        }
                        buf_val = value_map[key]
                    else:
                        buf_val = data["properties"][service][characteristic][key]
                    characteristic_data[characteristic][key] = buf_val
                if characteristic_data[characteristic]["value"] is None:
                    characteristic_data[characteristic]["value"] = characteristic_data[characteristic]["minValue"]
        return characteristic_data
