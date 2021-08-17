from typing import Optional

from gadgetlib import CharacteristicIdentifier
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher, GadgetDeletionError,\
    GadgetUpdateError, GadgetCreationError
from smarthome_bridge.gadget_update_connector import GadgetUpdateConnector
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator, \
    CharacteristicParsingError
from smarthome_bridge.gadget_publishers.homebridge_encoder import HomebridgeEncoder
from network.mqtt_credentials_container import MqttCredentialsContainer
from smarthome_bridge.gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from smarthome_bridge.gadget_publishers.homebridge_decoder import HomebridgeDecoder


# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts


class GadgetPublisherHomeBridge(GadgetPublisher):

    _network_connector: HomebridgeNetworkConnector

    def __init__(self, network_connector: HomebridgeNetworkConnector):
        super().__init__()
        self._network_connector = network_connector
        self._network_connector.attach_characteristic_update_callback(self._parse_characteristic_update)

    def __del__(self):
        super().__del__()
        self._network_connector.__del__()

    def remove_gadget(self, gadget_name: str):
        self._logger.info(f"Removing gadget '{gadget_name}' from external source")
        deletion_successful = self._network_connector.remove_gadget(gadget_name)
        if not deletion_successful:
            raise GadgetDeletionError(gadget_name)

    def create_gadget(self, gadget: Gadget):
        self._logger.info(f"Creating gadget '{gadget.get_name()}' from external source")
        adding_successful = self._network_connector.add_gadget(gadget)
        if not adding_successful:
            raise GadgetCreationError(gadget.get_name())
        for characteristic in gadget.get_characteristics():
            self._update_characteristic(gadget, characteristic.get_type())

    def _parse_characteristic_update(self, gadget_name: str, characteristic_name: str, value: int):
        self._logger.info(f"Received update for '{gadget_name}' on '{characteristic_name}': {value}")
        try:
            characteristic = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
        except CharacteristicParsingError as err:
            self._logger.error(err.args[0])
            return
        fetched_gadget = self._fetch_gadget_data(gadget_name)
        if fetched_gadget is None:
            return
        self._publish_update(fetched_gadget)

    @staticmethod
    def _gadget_needs_update(local_gadget: Gadget, fetched_gadget: Gadget):
        """
        Checks if the gadget on the remote storage needs an update by comparing the gadgets characteristics boundaries

        :param local_gadget: The local gadget (master)
        :param fetched_gadget: The fetched gadget to compare it with
        :return: Whether the fetched gadget needs to be updated
        """
        needs_update = local_gadget.get_characteristics() != fetched_gadget.get_characteristics()
        return needs_update

    def _fetch_gadget_data(self, gadget_name: str) -> Optional[Gadget]:
        """
        Tries to load a gadget from the remote storage

        :param gadget_name: Name of the gadget to fetch
        :return: The gadget if fetching was successful
        """
        fetched_gadget_data = self._network_connector.get_gadget_info(gadget_name)
        if fetched_gadget_data is not None:
            fetched_gadget = HomebridgeDecoder().decode_characteristics(gadget_name, fetched_gadget_data)
            if fetched_gadget is not None:
                return fetched_gadget
        return None

    def _update_characteristic(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        characteristic_value = gadget.get_characteristic(characteristic).get_true_value()
        characteristic_str = HomebridgeCharacteristicTranslator.type_to_string(characteristic)
        self._network_connector.update_characteristic(gadget.get_name(),
                                                      characteristic_str,
                                                      characteristic_value)

    def receive_update(self, gadget: Gadget):
        fetched_gadget = self._fetch_gadget_data(gadget.get_name())
        if fetched_gadget is None:
            # Gadget with given name does not exist on the remote system, or is broken somehow
            try:
                self.create_gadget(gadget)
            except GadgetCreationError as err:
                self._logger.error(err.args[0])
                raise GadgetUpdateError(gadget.get_name())
        else:
            if self._gadget_needs_update(gadget, fetched_gadget):
                # Gadget needs to be recreated due to characteristic boundaries changes
                try:
                    self.remove_gadget(gadget.get_name())
                except GadgetDeletionError as err:
                    self._logger.error(err.args[0])

                try:
                    self.create_gadget(gadget)
                except GadgetCreationError as err:
                    self._logger.error(err.args[0])
                    raise GadgetUpdateError(gadget.get_name())

            else:
                # Gadget does not need to be re-created, only updated
                for characteristic in gadget.get_characteristics():
                    fetched_characteristic = fetched_gadget.get_characteristic(characteristic.get_type())
                    if fetched_characteristic != characteristic:
                        self._update_characteristic(gadget, characteristic.get_type())
