import enum
import json
from typing import Optional

from lib.validator_interface import IValidator
from network.auth_container import CredentialsAuthContainer, SerialAuthContainer, MqttAuthContainer
from network.request import Request
from lib.pubsub import Subscriber
from smarthome_bridge.api.exceptions import AuthError
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.request_handler_bridge import RequestHandlerBridge
from smarthome_bridge.api.request_handler_client import RequestHandlerClient
from smarthome_bridge.api.request_handler_configs import RequestHandlerConfigs
from smarthome_bridge.api.request_handler_gadget import RequestHandlerGadget
from smarthome_bridge.api.request_handler_gadget_publisher import RequestHandlerGadgetPublisher
from smarthome_bridge.api.response_creator import ResponseCreator
from lib.logging_interface import ILogging
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from smarthome_bridge.status_supplier_interfaces.client_status_supplier import ClientStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier
from smarthome_bridge.update.bridge_update_manager import BridgeUpdateManager
from system.api_definitions import ApiURIs, ApiAccessLevel, ApiEndpointCategory
from utils.auth_manager import AuthManager, AuthenticationFailedException, InsufficientAccessPrivilegeException
from utils.client_config_manager import ClientConfigManager
from utils.user_manager import UserDoesNotExistException


class RequestDirection(enum.IntEnum):
    Incoming = 0
    Outgoing = 1
    Illegal = 2
    Unknown = 3


class ApiManagerSetupContainer:
    network: NetworkManager
    gadgets: GadgetStatusSupplier
    clients: ClientStatusSupplier
    publishers: GadgetPublisherStatusSupplier
    bridge: BridgeStatusSupplier
    auth: AuthManager
    updater: Optional[BridgeUpdateManager]
    configs: Optional[ClientConfigManager]

    def __init__(self, network: NetworkManager,
                 gadgets: GadgetStatusSupplier,
                 clients: ClientStatusSupplier,
                 publishers: GadgetPublisherStatusSupplier,
                 bridge: BridgeStatusSupplier,
                 auth: AuthManager,
                 updater: Optional[BridgeUpdateManager],
                 configs: Optional[ClientConfigManager]):
        self.network = network
        self.gadgets = gadgets
        self.clients = clients
        self.publishers = publishers
        self.bridge = bridge
        self.auth = auth
        self.updater = updater
        self.configs = configs


class ApiManager(Subscriber, ILogging, IValidator):
    _gadget_status_supplier: Optional[GadgetStatusSupplier]

    _network: NetworkManager

    _gadget_sync_connection: Optional[str]

    _auth_manager: Optional[AuthManager]

    _bridge_request_handler: RequestHandlerBridge
    _client_request_handler: RequestHandlerClient
    _gadget_request_handler: RequestHandlerGadget
    _configs_request_handler: RequestHandlerConfigs
    _gadget_publisher_request_handler: RequestHandlerGadgetPublisher

    def __init__(self, setup: ApiManagerSetupContainer):
        super().__init__()
        self._network = setup.network
        self._network.subscribe(self)
        self._gadget_sync_connection = None
        self._auth_manager = setup.auth

        self._bridge_request_handler = RequestHandlerBridge(self._network, setup.bridge, setup.updater)
        self._client_request_handler = RequestHandlerClient(self._network, setup.clients, setup.gadgets)
        self._gadget_request_handler = RequestHandlerGadget(self._network, setup.gadgets)
        self._configs_request_handler = RequestHandlerConfigs(self._network, setup.configs)
        self._gadget_publisher_request_handler = RequestHandlerGadgetPublisher(self._network, setup.publishers)

    def __del__(self):
        pass

    @property
    def auth_manager(self) -> AuthManager:
        return self._auth_manager

    @auth_manager.setter
    def auth_manager(self, value: AuthManager):
        self._auth_manager = value

    @property
    def request_handler_bridge(self) -> RequestHandlerBridge:
        return self._bridge_request_handler

    @property
    def request_handler_client(self) -> RequestHandlerClient:
        return self._client_request_handler

    @property
    def request_handler_gadget(self) -> RequestHandlerGadget:
        return self._gadget_request_handler

    @property
    def request_handler_configs(self) -> RequestHandlerConfigs:
        return self._configs_request_handler

    def receive(self, req: Request):
        self._log_request(req)

        direction_type = self._check_direction(req)
        if direction_type == RequestDirection.Incoming:
            self._handle_response(req)
        elif direction_type == RequestDirection.Outgoing:
            self._handle_request(req)
        elif direction_type == RequestDirection.Unknown:
            ResponseCreator.respond_with_error(req, "UnknownUriError", "Uri is not known")

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

        auth = req.get_auth()

        if auth is None:
            ResponseCreator.respond_with_error(req,
                                               "NeAuthError",
                                               "The bridge only accepts requests based on privileges")
            raise AuthError()

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
                raise TypeError("Illegal auth type ", auth.__class__.__name__)
        except AuthenticationFailedException:
            ResponseCreator.respond_with_error(req, "WrongAuthError", "illegal combination of username and password")
            raise AuthError()
        except UserDoesNotExistException:
            ResponseCreator.respond_with_error(req, "UserDoesntExistError", "User does not exist")
            raise AuthError()
        except InsufficientAccessPrivilegeException:
            ResponseCreator.respond_with_error(req, "AccessLevelError", "Insufficient privileges")
            raise AuthError()

    @staticmethod
    def _check_direction(req: Request) -> RequestDirection:
        """
        Checks the request's direction to determine if it needs handling

        :param req: Request to check
        :return: True if request needs to be handled
        """

        res_receiver_paths = [x.uri for x in ApiURIs.get_endpoints() if x.outgoing]
        if req.is_response and req.get_path() in res_receiver_paths:
            return RequestDirection.Incoming

        req_receiver_paths = [x.uri for x in ApiURIs.get_endpoints() if not x.outgoing]
        if not req.is_response and req.get_path() in req_receiver_paths:
            return RequestDirection.Outgoing

        if req.get_path() not in [x.uri for x in ApiURIs.get_endpoints()]:
            return RequestDirection.Unknown

        return RequestDirection.Illegal

    def _handle_request(self, req: Request):
        try:
            self._check_auth(req)
        except AuthError:
            return

        switcher = {
            ApiEndpointCategory.System: self._bridge_request_handler,
            ApiEndpointCategory.Gadgets: self._gadget_request_handler,
            ApiEndpointCategory.Publishers: self._gadget_publisher_request_handler,
            ApiEndpointCategory.Clients: self._client_request_handler,
            ApiEndpointCategory.Configs: self._configs_request_handler
        }

        endpoint_definition = ApiURIs.get_definition_for_uri(req.get_path())
        handler: RequestHandler = switcher.get(endpoint_definition.category)

        handler.handle_request(req)

        if ApiURIs.get_definition_for_uri(req.get_path()).requires_response and req.can_respond:
            ResponseCreator.respond_with_error(
                req,
                "NotImplementedError",
                f"The URI requested ({req.get_path()}) is known to the system but not implemented")

    def _handle_response(self, req: Request):
        pass  # TODO: handle responses to outgoing requests
