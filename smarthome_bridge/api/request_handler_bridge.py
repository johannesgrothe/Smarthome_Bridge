import os
from typing import Callable

from jsonschema.exceptions import ValidationError

from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.api_coders.bridge_encoder import BridgeEncoder
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces import BridgeStatusSupplier
from system.api_definitions import ApiURIs
from utils.bridge_update_manager import BridgeUpdateManager, UpdateNotSuccessfulException, NoUpdateAvailableException, \
    UpdateNotPossibleException


class RequestHandlerBridge(RequestHandler):
    _status_suppler: BridgeStatusSupplier

    def __init__(self, network: NetworkManager, status_supplier: BridgeStatusSupplier):
        super().__init__(network)
        self._status_suppler = status_supplier

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.info_bridge: self._handle_info_bridge,
            ApiURIs.bridge_update_check.uri: self._handle_check_bridge_for_update,
            ApiURIs.bridge_update_execute.uri: self._handle_bridge_update
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def _handle_info_bridge(self, req: Request):
        data = self._status_suppler.info
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

        try:
            updater = BridgeUpdateManager(os.getcwd())
            bridge_meta = updater.check_for_update()
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

        try:
            updater = BridgeUpdateManager(os.getcwd())
            updater.execute_update()
            ResponseCreator.respond_with_success(req, "Update was successful, rebooting system now...")
            updater.reboot()
        except UpdateNotSuccessfulException:
            ResponseCreator.respond_with_error(req, "UpdateNotSuccessfulException", "Update failed for some reason")
