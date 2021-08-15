from typing import Optional

from gadgetlib import CharacteristicIdentifier
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher, Gadget,\
    GadgetIdentifier, GadgetUpdateConnector
from smarthome_bridge.gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator
from smarthome_bridge.gadget_publishers.homebridge_encoder import HomebridgeEncoder
from network.mqtt_credentials_container import MqttCredentialsContainer
from smarthome_bridge.gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector


# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts


class GadgetPublisherHomeBridge(GadgetPublisher):

    _network_connector: HomebridgeNetworkConnector

    def __init__(self, update_connector: GadgetUpdateConnector, network_connector: HomebridgeNetworkConnector):
        super().__init__(update_connector)
        self._network_connector = network_connector
        self._network_connector.attach_characteristic_update_callback(self._parse_characteristic_update)

    def remove_gadget(self, gadget_name: str) -> bool:
        return self._network_connector.remove_gadget(gadget_name)

    def _parse_characteristic_update(self, gadget_name: str, characteristic_name: str, value: int):
        characteristic = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
        self._publish_characteristic_update(gadget_name, characteristic, value)

    def _compare_remote_with_local_gadget(self, gadget: Gadget, gadget_data: dict) -> bool:



    def handle_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier) -> bool:
        fetched_gadget_data = self._network_connector.get_gadget_info(gadget.get_name())

        characteristic_value = gadget.get_characteristic(characteristic).get_true_value()
        characteristic_str = HomebridgeCharacteristicTranslator.type_to_string(characteristic)
        return self._network_connector.update_characteristic(gadget.get_name(),
                                                             characteristic_str,
                                                             characteristic_value)

