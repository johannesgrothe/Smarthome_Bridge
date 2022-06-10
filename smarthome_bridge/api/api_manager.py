import json
import os
from typing import Optional, Callable
from jsonschema import ValidationError

from network.auth_container import CredentialsAuthContainer, SerialAuthContainer, MqttAuthContainer
from network.request import Request, NoClientResponseException
from lib.pubsub import Subscriber
from smarthome_bridge.gadget_status_supplier import GadgetStatusSupplier
from utils.json_validator import Validator

from lib.logging_interface import LoggingInterface
from smarthome_bridge.network_manager import NetworkManager

from gadgets.remote.remote_gadget import RemoteGadget

from utils.client_config_manager import ClientConfigManager, ConfigDoesNotExistException, ConfigAlreadyExistsException

from smarthome_bridge.api_encoder import ApiEncoder, GadgetEncodeError
from smarthome_bridge.api_decoder import ApiDecoder, GadgetDecodeError
from smarthome_bridge.api_manager_delegate import ApiManagerDelegate
from system.api_definitions import ApiURIs, ApiAccessLevel
from utils.auth_manager import AuthManager, AuthenticationFailedException, InsufficientAccessPrivilegeException, \
    UnknownUriException
from clients.client_controller import ClientController, ClientRebootError
from utils.user_manager import UserDoesNotExistException

from utils.bridge_update_manager import BridgeUpdateManager, UpdateNotPossibleException, NoUpdateAvailableException, \
    UpdateNotSuccessfulException


class UnknownClientException(Exception):
    def __init__(self, name: str):
        super(UnknownClientException, self).__init__(f"client with name: {name} does nee exist")


class AuthError(Exception):
    """Error raised if anything failed checking the authentication of an incoming request"""


class ApiManager(Subscriber, LoggingInterface):
    _validator: Validator

    _delegate: ApiManagerDelegate

    _gadget_status_supplier: Optional[GadgetStatusSupplier]

    _network: NetworkManager

    _gadget_sync_connection: Optional[str]

    _auth_manager: Optional[AuthManager]

    def __init__(self, delegate: ApiManagerDelegate, gadget_supplier: GadgetStatusSupplier, network: NetworkManager):
        super().__init__()
        self._delegate = delegate
        self._network = network
        self._network.subscribe(self)
        self._validator = Validator()
        self._gadget_sync_connection = None
        self.auth_manager = None
        self._gadget_status_supplier = gadget_supplier

    def __del__(self):
        pass

    @property
    def auth_manager(self) -> AuthManager:
        return self._auth_manager

    @auth_manager.setter
    def auth_manager(self, value: AuthManager):
        self._auth_manager = value

    def receive(self, req: Request):
        self._handle_request(req)

    def request_sync(self, name: str):
        self._logger.info(f"Requesting client sync information from '{name}'")
        self._network.send_request(ApiURIs.sync_request.uri, name, {}, 0)

    def _respond_with_error(self, req: Request, err_type: str, message: str):
        message = message.replace("\"", "'")
        req.respond({"error_type": err_type, "message": message})
        self._logger.error(f"{err_type}: {message}")

    def _respond_with_status(self, req: Request, ack: bool, message: Optional[str] = None):
        out_payload = {"ack": ack, "message": message}
        req.respond(out_payload)
        self._logger.info(f"Responding with status: {ack} to request: {req.get_path()}")

    def send_gadget_update(self, gadget: RemoteGadget):
        self._logger.info(f"Broadcasting gadget update information for '{gadget.get_name()}'")
        try:
            gadget_data = ApiEncoder().encode_gadget_update(gadget)
            self._network.send_broadcast(ApiURIs.update_gadget.uri,
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

    def _log_request(self, req: Request):
        short_json = json.dumps(req.get_payload())
        if len(short_json) > 35:
            short_json = short_json[:35] + f"... + {len(short_json) - 35} bytes"
        auth_type = "No Auth" if req.get_auth() is None else req.get_auth().__class__.__name__[:-13]
        self._logger.info(f"Received request from '{req.get_sender()}' at '{req.get_path()}' "
                          f"(Auth type: '{auth_type}'): {short_json}")

    def _check_auth(self, req: Request):
        if self.auth_manager is None:
            return

        if req.get_auth() is None:
            self._respond_with_error(req, "NeAuthError", "The bridge only accepts requests based on privileges")
            raise AuthError()

        auth = req.get_auth()
        try:
            if isinstance(auth, CredentialsAuthContainer):
                self.auth_manager.authenticate(auth.username, auth.password)
                self.auth_manager.check_path_access_level_for_user(auth.username,
                                                                   req.get_path())
            elif isinstance(auth, SerialAuthContainer):
                self.auth_manager.check_path_access_level(ApiAccessLevel.admin,
                                                          req.get_path())
            elif isinstance(auth, MqttAuthContainer):
                self.auth_manager.check_path_access_level(ApiAccessLevel.mqtt,
                                                          req.get_path())
            else:
                self._respond_with_error(req, "UnknownAuthError", "Unknown error occurred")
                raise AuthError()
        except AuthenticationFailedException:
            self._respond_with_error(req, "WrongAuthError", "illegal combination of username and password")
            raise AuthError()
        except UserDoesNotExistException:
            self._respond_with_error(req, "UserDoesntExistError", "User does not exist")
            raise AuthError()
        except InsufficientAccessPrivilegeException:
            self._respond_with_error(req, "AccessLevelError", "Insufficient privileges")
            raise AuthError()
        except UnknownUriException:
            self._handle_unknown(req)
            raise AuthError()

    @staticmethod
    def _check_direction(req: Request) -> bool:
        """
        Checks the request's direction to determine if it needs handling

        :param req: Request to check
        :return: True if request needs to be handled
        """
        res_receiver_paths = [x.uri for x in ApiURIs.get_endpoints() if x.outgoing]
        if req.is_response and req.get_path() in res_receiver_paths:
            return True

        req_receiver_paths = [x.uri for x in ApiURIs.get_endpoints() if not x.outgoing]
        if not req.is_response and req.get_path() in req_receiver_paths:
            return True

        return False

    def _handle_request(self, req: Request):
        self._log_request(req)

        if not self._check_direction(req):
            return

        try:
            self._check_auth(req)
        except AuthError:
            return

        switcher = {
            ApiURIs.heartbeat.uri: self._handle_heartbeat,
            ApiURIs.sync_client.uri: self._handle_client_sync,
            ApiURIs.info_bridge.uri: self._handle_info_bridge,
            ApiURIs.info_gadgets.uri: self._handle_info_gadgets,
            ApiURIs.info_clients.uri: self._handle_info_clients,
            ApiURIs.info_gadget_publishers.uri: self._handle_info_gadget_publishers,
            ApiURIs.update_gadget.uri: self._handle_update_gadget,
            ApiURIs.client_reboot.uri: self._handle_client_reboot,
            ApiURIs.client_config_write.uri: self._handle_client_config_write,
            ApiURIs.client_config_delete.uri: self._handle_client_config_delete,
            ApiURIs.config_storage_get_all.uri: self._handle_get_all_configs,
            ApiURIs.config_storage_get.uri: self._handle_get_config,
            ApiURIs.config_storage_save.uri: self._handle_save_config,
            ApiURIs.config_storage_delete.uri: self._handle_delete_config,
            ApiURIs.bridge_update_check.uri: self._handle_check_bridge_for_update,
            ApiURIs.bridge_update_execute.uri: self._handle_bridge_update
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), self._handle_unknown)
        handler(req)

    def _handle_unknown(self, req: Request):
        self._respond_with_error(req, "UnknownUriError", f"The URI requested ({req.get_path()}) does not exist")

    def _handle_info_bridge(self, req: Request):
        data = self._delegate.get_bridge_info()
        resp_data = ApiEncoder.encode_bridge_info(data)
        req.respond(resp_data)

    def _handle_info_gadget_publishers(self, req: Request):
        data = self._delegate.get_gadget_publisher_info()
        resp_data = ApiEncoder.encode_gadget_publisher_list(data)
        req.respond(resp_data)

    def _handle_info_gadgets(self, req: Request):
        resp_data = ApiEncoder().encode_all_gadgets_info(self._gadget_status_supplier.remote_gadgets,
                                                         self._gadget_status_supplier.local_gadgets)
        req.respond(resp_data)

    def _handle_info_clients(self, req: Request):
        data = self._delegate.get_client_info()
        resp_data = ApiEncoder().encode_all_clients_info(data)
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
            self._respond_with_error(req,
                                     "ValidationError",
                                     f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return

        gadget = self._gadget_status_supplier.get_gadget(req.get_payload()["id"])

        if gadget is None:
            self._respond_with_error(req, "GagdetDoesNeeExist", "Sadly, no gadget with the given id exists")
            return

        attributes = req.get_payload()["attributes"]
        gadget.name = req.get_payload()["name"]
        val_errs = []
        attr_errs = []
        self._logger.info(f"Updating {len(attributes)} attributes from '{req.get_sender()}'")
        for attr, value in req.get_payload()["attributes"].items():
            try:
                gadget.handle_attribute_update(attr, value)
            except ValueError as err:
                self._logger.warning(err.args[0])
                val_errs.append(attr)
            except IllegalAttributeError as err:
                self._logger.warning(err.args[0])
                attr_errs.append(attr)
        if val_errs or attr_errs:
            val_str = "No Value Errors"
            if val_errs:
                val_str = f"Value-Errors in [{', '.join(val_errs)}]"
            attr_str = "No Attribute Errors"
            if attr_errs:
                attr_str = f"Attribute-Errors in [{', '.join(attr_errs)}]"
            self._respond_with_error(req, "GadgetUpdateError", f"Problem while applying update: {val_str}, {attr_str}")
            return
        self._respond_with_status(req, True)

    def _handle_gadget(self, client_id: str, gadget_data: dict):
        """
        Takes the data from any sync request, creates a gadget out of it and gives it to the
        gadget manager for evaluation

        :param client_id: ID of the sending client
        :param gadget_data: JSON-data describing the gadget
        :return: None
        """
        try:
            gadget = ApiDecoder().decode_remote_gadget(gadget_data, client_id)
            self._gadget_status_supplier.
        except GadgetDecodeError as err:
            print(err.args[0])

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
                                     f"Request validation error at '{ApiURIs.update_gadget.uri}'")
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
                                     f"Request validation error at '{ApiURIs.update_gadget.uri}'")
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
                                     f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return
        # TODO: handle the request

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
                                     f"Request validation error at '{ApiURIs.config_storage_get_all.uri}'")
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
                                     f"Request validation error at '{ApiURIs.config_storage_get.uri}'")
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
                                     f"Request validation error at '{ApiURIs.config_storage_save.uri}'")
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
                                     f"Request validation error at '{ApiURIs.config_storage_delete.uri}'")
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
                                     f"Request validation error at {ApiURIs.bridge_update_check.uri}")
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
                                     f"Request validation error at {ApiURIs.bridge_update_execute.uri}")
            return

        try:
            updater = BridgeUpdateManager(os.getcwd())
            updater.execute_update()
            self._respond_with_status(req, True, "Update was successful, rebooting system now...")
            updater.reboot()
        except UpdateNotSuccessfulException:
            self._respond_with_error(req, "UpdateNotSuccessfulException", "Update failed for some reason")
