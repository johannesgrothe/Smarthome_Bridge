from typing import Optional

from gadgetlib import CharacteristicIdentifier
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher, GadgetDeletionError,\
    CharacteristicUpdateError, GadgetCreationError
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator
from smarthome_bridge.gadget_publishers.homebridge_encoder import HomebridgeEncoder
from network.mqtt_credentials_container import MqttCredentialsContainer
from smarthome_bridge.gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from smarthome_bridge.gadget_publishers.homebridge_decoder import HomebridgeDecoder


# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts


class GadgetPublisherHomeBridge(GadgetPublisher):

    _network_connector: HomebridgeNetworkConnector

    def __init__(self, update_connector: GadgetUpdateConnector, network_connector: HomebridgeNetworkConnector):
        super().__init__(update_connector)
        self._network_connector = network_connector
        self._network_connector.attach_characteristic_update_callback(self._parse_characteristic_update)

    def remove_gadget(self, gadget_name: str):
        deletion_successful = self._network_connector.remove_gadget(gadget_name)
        if not deletion_successful:
            raise GadgetDeletionError(gadget_name)

    def create_gadget(self, gadget: Gadget):
        adding_successful = self._network_connector.add_gadget(gadget)
        if not adding_successful:
            raise GadgetCreationError(gadget.get_name())

    def _parse_characteristic_update(self, gadget_name: str, characteristic_name: str, value: int):
        characteristic = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
        self._publish_characteristic_update(gadget_name, characteristic, value)

    @staticmethod
    def _gadget_needs_update(local_gadget: Gadget, fetched_gadget: Gadget):
        return local_gadget.get_characteristics() == fetched_gadget.get_characteristics()

    def handle_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        fetched_gadget_data = self._network_connector.get_gadget_info(gadget.get_name())
        if fetched_gadget_data is None:
            try:
                self.create_gadget(gadget)
            except GadgetCreationError as err:
                self._logger.error(err.args[0])
                raise CharacteristicUpdateError(gadget.get_name(), characteristic)
        else:
            fetched_gadget = HomebridgeDecoder().decode_characteristics(gadget.get_name(), fetched_gadget_data)
            if fetched_gadget_data is None:
                try:
                    self.create_gadget(gadget)
                except GadgetCreationError as err:
                    self._logger.error(err.args[0])
                    raise CharacteristicUpdateError(gadget.get_name(), characteristic)
            else:
                if self._gadget_needs_update(gadget, fetched_gadget):
                    try:
                        self.remove_gadget(gadget.get_name())
                    except GadgetDeletionError as err:
                        self._logger.error(err.args[0])

                    try:
                        self.create_gadget(gadget)
                    except GadgetCreationError as err:
                        self._logger.error(err.args[0])
                        raise CharacteristicUpdateError(gadget.get_name(), characteristic)

                else:
                    characteristic_value = gadget.get_characteristic(characteristic).get_true_value()
                    characteristic_str = HomebridgeCharacteristicTranslator.type_to_string(characteristic)
                    update_successful = self._network_connector.update_characteristic(gadget.get_name(),
                                                                                      characteristic_str,
                                                                                      characteristic_value)
                    if not update_successful:
                        raise CharacteristicUpdateError(gadget.get_name(), characteristic)
