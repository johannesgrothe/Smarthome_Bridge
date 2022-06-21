import json
from typing import Optional, Callable

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
from system.api_definitions import ApiURIs, ApiAccessLevel, ApiEndpointCategory
from utils.auth_manager import AuthManager, AuthenticationFailedException, InsufficientAccessPrivilegeException, \
    UnknownUriException
from utils.user_manager import UserDoesNotExistException


class ApiManagerSetupContainer:
    network: NetworkManager
    gadgets: GadgetStatusSupplier
    clients: ClientStatusSupplier
    publishers: GadgetPublisherStatusSupplier
    bridge: BridgeStatusSupplier
    auth: AuthManager

    def __init__(self, network: NetworkManager,
                 gadgets: GadgetStatusSupplier,
                 clients: ClientStatusSupplier,
                 publishers: GadgetPublisherStatusSupplier,
                 bridge: BridgeStatusSupplier,
                 auth: AuthManager):
        self.network = network
        self.gadgets = gadgets
        self.clients = clients
        self.publishers = publishers
        self.bridge = bridge
        self.auth = auth


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

        self._bridge_request_handler = RequestHandlerBridge(self._network, setup.bridge)
        self._client_request_handler = RequestHandlerClient(self._network, setup.clients, setup.gadgets)
        self._gadget_request_handler = RequestHandlerGadget(self._network, setup.gadgets)
        self._configs_request_handler = RequestHandlerConfigs(self._network)
        self._gadget_publisher_request_handler = RequestHandlerGadgetPublisher(self._network, setup.publishers)

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
            ResponseCreator.respond_with_error(req,
                                               "NeAuthError",
                                               "The bridge only accepts requests based on privileges")
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
                ResponseCreator.respond_with_error(req, "UnknownAuthError", "Unknown error occurred")
                raise AuthError()
        except AuthenticationFailedException:
            ResponseCreator.respond_with_error(req, "WrongAuthError", "illegal combination of username and password")
            raise AuthError()
        except UserDoesNotExistException:
            ResponseCreator.respond_with_error(req, "UserDoesntExistError", "User does not exist")
            raise AuthError()
        except InsufficientAccessPrivilegeException:
            ResponseCreator.respond_with_error(req, "AccessLevelError", "Insufficient privileges")
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
            ApiEndpointCategory.System: self._bridge_request_handler,
            ApiEndpointCategory.Gadgets: self._gadget_request_handler,
            ApiEndpointCategory.Publishers: self._gadget_publisher_request_handler,
            ApiEndpointCategory.Clients: self._client_request_handler,
            ApiEndpointCategory.Configs: self._configs_request_handler
        }

        endpoint_definition = ApiURIs.get_definition_for_uri(req.get_path())
        handler: RequestHandler = switcher.get(endpoint_definition.category)
        if handler is None:
            ResponseCreator.respond_with_error(req,
                                               "UnknownUriError",
                                               f"The URI requested ({req.get_path()}) does not exist")
            return

        handler.handle_request(req)

        if req.can_respond:
            ResponseCreator.respond_with_error(req,
                                               "NotImplementedError",
                                               f"The URI requested ({req.get_path()}) is known to the system but not implemented")
