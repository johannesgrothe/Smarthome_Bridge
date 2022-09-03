from typing import Callable, Optional

from jsonschema.exceptions import ValidationError

from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.api_encoders.bridge_encoder import BridgeEncoder
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from system.api_definitions import ApiURIs
from smarthome_bridge.update.bridge_update_manager import BridgeUpdateManager, UpdateNotSuccessfulException, \
    NoUpdateAvailableException, UpdateNotPossibleException
from utils.user_manager import UserManager, UserAlreadyExistsException, UserCreationNotPossibleException


class RequestHandlerBridge(RequestHandler):
    _status_supplier: BridgeStatusSupplier
    _updater: Optional[BridgeUpdateManager]
    _user_manager: UserManager

    def __init__(self, network: NetworkManager, status_supplier: BridgeStatusSupplier,
                 update_manager: Optional[BridgeUpdateManager], user_manager: UserManager):
        super().__init__(network)
        self._status_supplier = status_supplier
        self._updater = update_manager
        self._user_manager = user_manager

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.info_bridge.uri: self._handle_info_bridge,
            ApiURIs.bridge_update_check.uri: self._handle_check_bridge_for_update,
            ApiURIs.bridge_update_execute.uri: self._handle_bridge_update,
            ApiURIs.bridge_add_user.uri: self._handle_bridge_add_user,
            ApiURIs.test_echo.uri: self._handle_echo
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def _handle_info_bridge(self, req: Request):
        data = self._status_supplier.info
        resp_data = BridgeEncoder.encode_bridge_info(data)
        req.respond(resp_data)

    def _handle_check_bridge_for_update(self, req: Request):
        """
        Checks whether the remote, the bridge is currently running on, is an older version

        :param req: empty request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_empty_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at {ApiURIs.bridge_update_check.uri}")
            return

        if not self._updater:
            ResponseCreator.respond_with_error(req, "UpdateNotPossibleException", "no updater configured")
            return

        try:
            bridge_meta = self._updater.check_for_update()
        except UpdateNotPossibleException:
            ResponseCreator.respond_with_error(req, "UpdateNotPossibleException", "bridge could not be updated")
        except NoUpdateAvailableException:
            ResponseCreator.respond_with_success(req, "Bridge is up to date")
        else:
            payload = BridgeEncoder.encode_bridge_update_info(bridge_meta)
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
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at {ApiURIs.bridge_update_execute.uri}")
            return

        if not self._updater:
            ResponseCreator.respond_with_error(req, "UpdateNotPossibleException", "no updater configured")
            return

        try:
            self._updater.execute_update()
            ResponseCreator.respond_with_success(req, "Update was successful, rebooting system now...")
            self._updater.reboot()
        except UpdateNotSuccessfulException:
            ResponseCreator.respond_with_error(req, "UpdateNotSuccessfulException", "Update failed for some reason")

    def _handle_bridge_add_user(self, req: Request):
        """
        Adds a user to the Bridge

        :param req: Request containing user info
        :return:
        """
        try:
            self._validator.validate(req.get_payload(), "api_bridge_add_user")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at {ApiURIs.bridge_add_user.uri}")
            return

        if not self._user_manager:
            ResponseCreator.respond_with_error(req, "UserCreationNotPossibleException", "no user manager configured")
            return

        user_info = req.get_payload()

        try:
            self._user_manager.add_user(user_info['username'], user_info['password'], user_info['access_level'],
                                        user_info['persistent'])
            ResponseCreator.respond_with_success(req, f"User: {user_info['username']} was successfully added")
        except UserAlreadyExistsException:
            ResponseCreator.respond_with_error(req, "UserAlreadyExistsException",
                                               f"user: {user_info['username']} already exists")
        except UserCreationNotPossibleException:
            ResponseCreator.respond_with_error(req, "UserCreationNotPossibleException",
                                               f"adding the user: {user_info['username']} was not possible")

    def _handle_echo(self, req: Request):
        """
        Responds with the same payload as it received

        :param req: any Request
        :return: None
        """
        req.respond(req.get_payload())
