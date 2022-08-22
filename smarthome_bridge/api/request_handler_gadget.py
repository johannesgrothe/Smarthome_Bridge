from typing import Callable

from jsonschema.exceptions import ValidationError
from gadgets.gadget_update_container import GadgetUpdateContainer
from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.api_encoders.gadget_api_encoder import GadgetEncodeError, GadgetApiEncoder
from smarthome_bridge.gadget_update_appliers.gadget_update_applier import GadgetUpdateApplier
from smarthome_bridge.gadget_update_appliers.gadget_update_applier_super import UpdateApplyError
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.gadget_status_receiver import GadgetStatusReceiver
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier
from system.api_definitions import ApiURIs

# TODO: Make RequestHandlerGadget full GadgetPublisher
from test_helpers.dummy_gadget_update_applier import DummyGadgetUpdateApplier


class RequestHandlerGadget(RequestHandler, GadgetStatusReceiver):
    _gadget_manager: GadgetStatusSupplier
    _update_applier: GadgetUpdateApplier

    def __init__(self, network: NetworkManager, gadget_manager: GadgetStatusSupplier):
        super().__init__(network)
        self._gadget_manager = gadget_manager
        self._gadget_manager.subscribe(self)
        self._update_applier = GadgetUpdateApplier()

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.info_gadgets.uri: self._handle_info_gadgets,
            ApiURIs.update_gadget.uri: self._handle_gadget_update,
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        self._logger.info(f"Broadcasting gadget update information for '{update_container.origin}'")
        source_gadget = self._gadget_manager.get_gadget(update_container.origin)
        gadget_data = GadgetApiEncoder.encode_gadget_update(update_container, source_gadget)
        self._network.send_broadcast(ApiURIs.update_gadget.uri,
                                     gadget_data,
                                     0)

    def add_gadget(self, gadget_id: str):
        pass  # TODO: notify connected clients that a gadget was created

    def remove_gadget(self, gadget_id: str):
        pass  # TODO: notify connected clients that a gadget was deleted

    def _handle_info_gadgets(self, req: Request):
        resp_data = GadgetApiEncoder.encode_all_gadgets_info(self._gadget_manager.remote_gadgets,
                                                             self._gadget_manager.local_gadgets)
        req.respond(resp_data)

    def _handle_gadget_update(self, req: Request):
        """
        Handles a characteristic update request, for a gadget, from any foreign source

        :param req: Request containing the gadget update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_gadget_update")
        except ValidationError:
            ResponseCreator.respond_with_error(req,
                                               "ValidationError",
                                               f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return

        payload = req.get_payload()
        gadget = self._gadget_manager.get_gadget(payload["id"])

        if gadget is None:
            ResponseCreator.respond_with_error(req, "GagdetDoesNeeExist", "Sadly, no gadget with the given id exists")
            return

        try:
            self._update_applier.apply(gadget, payload)
        except UpdateApplyError as err:
            ResponseCreator.respond_with_error(req, "GadgetUpdateApplyError", err.args[0])
            return

        ResponseCreator.respond_with_success(req)
