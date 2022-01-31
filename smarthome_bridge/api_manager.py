import os
from typing import Optional, Callable

from gadgets.any_gadget import AnyGadget
from network.request import Request, NoClientResponseException
from pubsub import Subscriber
from json_validator import Validator, ValidationError

from logging_interface import LoggingInterface
from smarthome_bridge.network_manager import NetworkManager

from gadgets.gadget import Gadget

from client_config_manager import ClientConfigManager, ConfigDoesNotExistException, ConfigAlreadyExistsException

from smarthome_bridge.api_encoder import ApiEncoder, GadgetEncodeError
from smarthome_bridge.api_decoder import ApiDecoder, GadgetDecodeError, ClientDecodeError
from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from system.api_definitions import ApiURIs
from clients.client_controller import ClientController, ClientRebootError

from bridge_update_manager import BridgeUpdateManager, UpdateNotPossibleException, NoUpdateAvailableException, \
    UpdateNotSuccessfulException


class UnknownClientException(Exception):
    def __init__(self, name: str):
        super(UnknownClientException, self).__init__(f"client with name: {name} does nee exist")


class ApiManager(Subscriber, LoggingInterface):
    _validator: Validator

    _delegate: ApiManagerDelegate

    _network: NetworkManager

    _gadget_sync_connection: Optional[str]

    def __init__(self, delegate: ApiManagerDelegate, network: NetworkManager):
        super().__init__()
        self._delegate = delegate
        self._network = network
        self._network.subscribe(self)
        self._validator = Validator()
        self._gadget_sync_connection = None

    def __del__(self):
        pass

    def receive(self, req: Request):
        self._handle_request(req)

    def request_sync(self, name: str):
        self._network.send_request(ApiURIs.sync_request.value, name, {}, 0)

    def _respond_with_error(self, req: Request, err_type: str, message: str):
        message = message.replace("\"", "'")
        req.respond({"error_type": err_type, "message": message})
        self._logger.error(f"{err_type}: {message}")

    def _respond_with_status(self, req: Request, ack: bool, message: Optional[str] = None):
        out_payload = {"ack": ack, "message": message}
        req.respond(out_payload)
        self._logger.info(f"responding with status: {ack} to request: {req.get_path()}")

    def send_gadget_update(self, gadget: Gadget):
        try:
            gadget_data = ApiEncoder().encode_gadget_update(gadget)
            self._network.send_broadcast(ApiURIs.update_gadget.value,
                                         gadget_data,
                                         0)
        except GadgetEncodeError as err:
            self._logger.error(err.args[0])

    def send_client_reboot(self, client_id: str):
        """
        Triggers the reboot of the specified client

        :param client_id: ID of the client
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises NoClientResponseException: If client did not respond to the request
        :raises ClientRebootError: If client could not be rebooted for aby reason
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.reboot_client()

    def send_client_system_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a system config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_system_config(config)

    def send_client_event_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a event config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_event_config(config)

    def send_client_gadget_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a gadget config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_gadget_config(config)

    def _handle_request(self, req: Request):
        self._logger.info(f"Received Request at {req.get_path()}")
        switcher = {
            ApiURIs.heartbeat.value: self._handle_heartbeat,
            ApiURIs.sync_client.value: self._handle_client_sync,
            ApiURIs.info_bridge.value: self._handle_info_bridge,
            ApiURIs.info_gadgets.value: self._handle_info_gadgets,
            ApiURIs.info_clients.value: self._handle_info_clients,
            ApiURIs.update_gadget.value: self._handle_update_gadget,
            ApiURIs.client_reboot.value: self._handle_client_reboot,
            ApiURIs.client_config_write.value: self._handle_client_config_write,
            ApiURIs.client_config_delete.value: self._handle_client_config_delete,
            ApiURIs.config_storage_get_all.value: self._handle_get_all_configs,
            ApiURIs.config_storage_get.value: self._handle_get_config,
            ApiURIs.config_storage_save.value: self._handle_save_config,
            ApiURIs.config_storage_delete.value: self._handle_delete_config,
            ApiURIs.bridge_update_check.value: self._handle_check_bridge_for_update,
            ApiURIs.bridge_update_execute.value: self._handle_bridge_update
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), self._handle_unknown)
        handler(req)

    def _handle_unknown(self, req: Request):
        self._logger.error(f"Received request at undefined path '{req.get_path()}'")

    def _handle_heartbeat(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_heartbeat_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{ApiURIs.heartbeat.value}'")
            return

        rt_id = req.get_payload()["runtime_id"]
        self._delegate.handle_heartbeat(req.get_sender(), rt_id)

    def _handle_client_sync(self, req: Request):
        """
        Handles a client update request from any foreign source

        :param req: Request containing the client update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_sync_request")
        except ValidationError as err:
            self._respond_with_error(req,
                                     "ValidationError",
                                     f"Request validation error at '{ApiURIs.sync_client.value}': '{err.message}'")
            return

        client_id = req.get_sender()

        self._logger.info(f"Syncing client {client_id}")

        decoder = ApiDecoder()

        new_client = decoder.decode_client(req.get_payload()["client"], req.get_sender())

        gadget_data = req.get_payload()["gadgets"]

        for gadget in gadget_data:
            self._update_gadget(client_id, gadget)

        self._delegate.handle_client_sync(new_client)

    def _handle_info_bridge(self, req: Request):
        data = self._delegate.get_bridge_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_bridge_info(data)
        req.respond(resp_data)

    def _handle_info_gadgets(self, req: Request):
        data = self._delegate.get_gadget_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_all_gadgets_info(data)
        req.respond(resp_data)

    def _handle_info_clients(self, req: Request):
        data = self._delegate.get_client_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_all_clients_info(data)
        req.respond(resp_data)

    def _handle_update_gadget(self, req: Request):
        """
        Handles a characteristic update request, for a gadget, from any foreign source

        :param req: Request containing the gadget update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_gadget_update_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.update_gadget.value}'")
            return

        try:
            gadget_update_info = ApiDecoder().decode_gadget_update(req.get_payload())
        except GadgetDecodeError:
            self._respond_with_error(req,
                                     "GadgetDecodeError",
                                     f"Gadget update decode error at '{ApiURIs.sync_client.value}'")
            return

        client_id = req.get_sender()

        gadget_info = [x for x in self._delegate.get_gadget_info() if x.get_name() == req.get_payload()["id"]]
        if not gadget_info:
            self._respond_with_error(req, "GagdetDoesNeeExist", "Sadly, no gadget with the given id exists")
            return

        gadget = gadget_info[0]

        updated_characteristics = [x.id for x in gadget_update_info.characteristics]
        buf_characteristics = [x for x in gadget.get_characteristics() if x.get_type() in updated_characteristics]

        for c in buf_characteristics:
            value = [x.step_value for x in gadget_update_info.characteristics if x.id == c.get_type()][0]
            c.set_step_value(value)

        out_gadget = AnyGadget(gadget_update_info.id,
                               req.get_sender(),
                               buf_characteristics)

        self._logger.info(f"Updating {len(buf_characteristics)} gadget characteristics from '{client_id}'")
        self._delegate.handle_gadget_update(out_gadget)

    def _handle_client_reboot(self, req: Request):
        """
        Handles a client reboot request

        :param req: Request containing the client id to reboot
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_reboot_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.update_gadget.value}'")
            return
        try:
            self.send_client_reboot(req.get_payload()["id"])
        except UnknownClientException:
            self._respond_with_error(req,
                                     "UnknownClientException",
                                     f"Nee client with the id: {req.get_payload()['id']} exists")
        except NoClientResponseException:
            self._respond_with_error(req,
                                     "NoClientResponseException",
                                     f"Client did not respond to reboot request")
        except ClientRebootError:
            self._respond_with_error(req,
                                     "ClientRebootError",
                                     f"Client could not be rebooted for some reason")

    def _handle_client_config_write(self, req: Request):
        """
        Handles a client config write request
        :param req: Request containing the client config to write
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_config_write")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.update_gadget.value}'")
            return
        # TODO: handle the request

    def _handle_client_config_delete(self, req: Request):
        """
        Handles a client config delete request
        :param req: Request containing the client config to delete
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_config_delete")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.update_gadget.value}'")
            return
        # TODO: handle the request

    def _update_gadget(self, client_id: str, gadget_data: dict):
        """
        Takes the data from any sync request, creates a gadget out of it and gives it to the
        gadget manager for evaluation

        :param client_id: ID of the sending client
        :param gadget_data: JSON-data describing the gadget
        :return: None
        """

        decoder = ApiDecoder()

        try:
            buf_gadget = decoder.decode_gadget(gadget_data, client_id)
            self._delegate.handle_gadget_sync(buf_gadget)

        except GadgetDecodeError as err:
            self._logger.error(err.args[0])
            return

    def _handle_get_all_configs(self, req: Request):
        """
        Responds with the names and descriptions of all available configs

        :param req: empty Request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_empty_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.config_storage_get_all.value}'")
            return

        manager = ClientConfigManager()
        config_names = manager.get_config_names()
        all_configs = {}
        self._logger.info("fetching all configs")
        for config in config_names:
            if not config == "Example":
                try:
                    conf = manager.get_config(config)
                    all_configs[config] = conf["description"]
                except ConfigDoesNotExistException:
                    self._logger.error("congratz, something went wrong, abort, abort, return to the moon base")
                    pass
            else:
                pass
        payload = {"configs": all_configs}
        req.respond(payload)

    def _handle_get_config(self, req: Request):
        """
        Responds with the config for a given name, if there is none an error is returned

        :param req: Request containing the name of the requested config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_delete_get")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.config_storage_get.value}'")
            return

        try:
            name = req.get_payload()["name"]
            config = ClientConfigManager().get_config(name)
            payload = {"config": config}
            req.respond(payload)
        except ConfigDoesNotExistException as err:
            self._respond_with_error(req=req, err_type="ConfigDoesNotExistException", message=err.args[0])

    def _handle_save_config(self, req: Request):
        """
        Saves the given config or overwrites an already existing config

        :param req: Request containing the config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_save")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.config_storage_save.value}'")
            return

        config = req.get_payload()["config"]
        overwrite = req.get_payload()["overwrite"]
        manager = ClientConfigManager()
        try:
            manager.write_config(config, overwrite=overwrite)
        except ConfigAlreadyExistsException as err:
            self._respond_with_error(req=req, err_type="ConfigAlreadyExistsException", message=err.args[0])
            return
        self._respond_with_status(req, True, "Config was saved successfully")

    def _handle_delete_config(self, req: Request):
        """
        Deletes the config for a given name, if there is no config, an error is returned

        :param req: Request containing name of the config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_delete_get")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at '{ApiURIs.config_storage_delete.value}'")
            return

        name = req.get_payload()["name"]
        manager = ClientConfigManager()
        try:
            manager.delete_config_file(name)
        except ConfigDoesNotExistException as err:
            self._respond_with_error(req=req, err_type="ConfigDoesNotExistException", message=err.args[0])
            return
        self._respond_with_status(req, True, "Config was deleted successfully")

    def _handle_check_bridge_for_update(self, req: Request):
        """
        Checks whether the remote, the bridge is currently running on, is an older version

        :param req: empty request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_empty_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at {ApiURIs.bridge_update_check.value}")
            return

        encoder = ApiEncoder()
        try:
            updater = BridgeUpdateManager(os.getcwd())
            bridge_meta = updater.check_for_update()
        except UpdateNotPossibleException:
            self._respond_with_error(req, "UpdateNotPossibleException", "bridge could not be updated")
        except NoUpdateAvailableException:
            self._respond_with_status(req, True, "Bridge is up to date")
        else:
            payload = encoder.encode_bridge_update_info(bridge_meta)
            req.respond(payload)
            return

    def _handle_bridge_update(self, req: Request):
        """
        Updates the Bridge to a newer version or another remote, remote has to be specified in request

        :param req: empty Request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_empty_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError",
                                     f"Request validation error at {ApiURIs.bridge_update_execute.value}")
            return

        try:
            updater = BridgeUpdateManager(os.getcwd())
            updater.execute_update()
            self._respond_with_status(req, True, "Update was successful, rebooting system now...")
            updater.reboot()
        except UpdateNotSuccessfulException:
            self._respond_with_error(req, "UpdateNotSuccessfulException", "Update failed for some reason")
