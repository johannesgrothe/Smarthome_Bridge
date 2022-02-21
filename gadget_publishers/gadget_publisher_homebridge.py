import datetime
import threading
from typing import Optional
from copy import deepcopy

from system.gadget_definitions import CharacteristicIdentifier
from gadget_publishers.gadget_publisher import GadgetPublisher, GadgetDeletionError, \
    GadgetUpdateError, GadgetCreationError
from gadgets.gadget import Gadget
from gadgets.any_gadget import AnyGadget
from gadget_publishers.homebridge_characteristic_translator import HomebridgeCharacteristicTranslator, \
    CharacteristicParsingError
from gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from gadget_publishers.homebridge_decoder import HomebridgeDecoder
from utils.thread_manager import ThreadManager

# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts


# Time to store updated before forwarding them in ms
_send_delay = 100


class QueuedGadgetUpdate:
    timestamp: datetime.datetime
    gadget: AnyGadget

    def __init__(self, timestamp: datetime.datetime, gadget: AnyGadget):
        self.timestamp = timestamp
        self.gadget = gadget


class GadgetPublisherHomeBridge(GadgetPublisher):
    _network_connector: HomebridgeNetworkConnector
    _queued_updates: list[QueuedGadgetUpdate]
    _update_lock: threading.Lock
    _thread_manager: ThreadManager

    def __init__(self, network_connector: HomebridgeNetworkConnector):
        super().__init__()
        self._network_connector = network_connector
        self._queued_updates = []
        self._update_lock = threading.Lock()
        self._thread_manager = ThreadManager()
        self._network_connector.attach_characteristic_update_callback(self._parse_characteristic_update)
        self._thread_manager.add_thread("Gadget Update Management", self._manage_queued_updates)
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        self._network_connector.__del__()
        self._thread_manager.__del__()

    def _manage_queued_updates(self):
        now = datetime.datetime.now()
        outgoing_update = None
        with self._update_lock:
            for update in self._queued_updates:
                if update.timestamp + datetime.timedelta(milliseconds=_send_delay) > now:
                    outgoing_update = update.gadget
                    self._queued_updates.remove(update)
                    break
        if outgoing_update is not None:
            self._publish_gadget_update(outgoing_update)

    def _add_update_to_queue(self, gadget: AnyGadget):
        with self._update_lock:
            new_gadget = gadget
            for update in self._queued_updates:
                if update.gadget.get_name() == gadget.get_name():
                    gadget_cs = gadget.get_characteristics()
                    new_c_types = [x.get_type() for x in gadget_cs]
                    update_cs = update.gadget.get_characteristics()
                    joined_characteristics = gadget_cs + [x for x in update_cs if x.get_type() not in new_c_types]
                    new_gadget = AnyGadget(gadget.get_name(), gadget.get_host_client(), joined_characteristics)
                    self._queued_updates.remove(update)
                    break
            new_entry = QueuedGadgetUpdate(datetime.datetime.now(), new_gadget)
            self._queued_updates.append(new_entry)

    def remove_gadget(self, gadget_name: str):
        self._logger.info(f"Removing gadget '{gadget_name}' from external source")
        deletion_successful = self._network_connector.remove_gadget(gadget_name)
        if not deletion_successful:
            raise GadgetDeletionError(gadget_name)

    def create_gadget(self, gadget: Gadget):
        self._logger.info(f"Creating gadget '{gadget.get_name()}' on external source")
        adding_successful = self._network_connector.add_gadget(gadget)
        if not adding_successful:
            raise GadgetCreationError(gadget.get_name())
        for characteristic in gadget.get_characteristics():
            self._update_characteristic(gadget, characteristic.get_type())

    def _parse_characteristic_update(self, gadget_name: str, characteristic_name: str, value: int):
        self._logger.info(f"Received update for '{gadget_name}' on '{characteristic_name}': {value}")
        try:
            c_type = HomebridgeCharacteristicTranslator.str_to_type(characteristic_name)
        except CharacteristicParsingError as err:
            self._logger.error(err.args[0])
            return

        buf_gadget = self._status_supplier.get_gadget(gadget_name)
        if buf_gadget is None:
            self._logger.error(f"Cannot apply status change to gadget '{gadget_name}' because it does not exist")
            return

        characteristic = buf_gadget.get_characteristic(c_type)
        if characteristic is None:
            self._logger.error(f"Cannot apply status change to gadget '{gadget_name}' "
                               f"because it does not have the required characteristic")
            return

        characteristic = deepcopy(characteristic)

        characteristic.set_true_value(value)

        out_gadget = AnyGadget(gadget_name,
                               "any",
                               [characteristic])

        self._add_update_to_queue(out_gadget)

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
            fetched_characteristics = HomebridgeDecoder().decode_characteristics(fetched_gadget_data)
            fetched_gadget = AnyGadget(gadget_name, "any", fetched_characteristics)
            return fetched_gadget
        return None

    def _update_characteristic(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        """
        Updates a specific characteristic on from the gadget on the remote storage

        :param gadget: Gadget to get characteristic information from
        :param characteristic: Characteristic to update
        :return: None
        :raises CharacteristicParsingError: If selected characteristic could not be parsed correctly
        """
        characteristic_value = gadget.get_characteristic(characteristic).get_true_value()
        characteristic_str = HomebridgeCharacteristicTranslator.type_to_string(characteristic)
        self._network_connector.update_characteristic(gadget.get_name(),
                                                      characteristic_str,
                                                      characteristic_value)

    def receive_gadget_update(self, gadget: Gadget):
        for identifier in [x.get_type() for x in gadget.get_characteristics()]:
            try:
                self._update_characteristic(gadget, identifier)
            except CharacteristicParsingError as err:
                self._logger.info(err.args[0])

    def receive_gadget(self, gadget: Gadget):
        if self._last_published_gadget is not None and self._last_published_gadget == gadget.get_name():
            return
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
                    if fetched_characteristic.get_true_value() != characteristic.get_true_value():
                        self._update_characteristic(gadget, characteristic.get_type())
