from typing import Callable

from jsonschema.exceptions import ValidationError

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.api_coders.gadget_api_encoder import GadgetApiEncoder
from smarthome_bridge.api_encoder import ApiEncoder, GadgetEncodeError
from smarthome_bridge.gadget_status_supplier import GadgetStatusReceiver, GadgetStatusSupplier
from smarthome_bridge.network_manager import NetworkManager
from system.api_definitions import ApiURIs


class RequestHandlerGadget(RequestHandler, GadgetStatusReceiver):

    _gadget_manager: GadgetStatusSupplier

    def __init__(self, network: NetworkManager, gadget_manager: GadgetStatusSupplier):
        super().__init__(network)
        self._gadget_manager = gadget_manager
        self._gadget_manager.subscribe(self)

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
        try:
            source_gadget = self._gadget_manager.get_gadget(update_container.origin)
            gadget_data = GadgetApiEncoder.encode_gadget_update(update_container, source_gadget)
            self._network.send_broadcast(ApiURIs.update_gadget.uri,
                                         gadget_data,
                                         0)
        except GadgetEncodeError as err:
            self._logger.error(err.args[0])

    def _handle_info_gadgets(self, req: Request):
        resp_data = ApiEncoder().encode_all_gadgets_info(self._gadget_manager.remote_gadgets,
                                                         self._gadget_manager.local_gadgets)
        req.respond(resp_data)

    def _handle_gadget_update(self, req: Request):
        """
        Handles a characteristic update request, for a gadget, from any foreign source

        :param req: Request containing the gadget update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_gadget_update_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req,
                                               "ValidationError",
                                               f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return

        gadget = self._gadget_manager.get_gadget(req.get_payload()["id"])

        if gadget is None:
            ResponseCreator.respond_with_error(req, "GagdetDoesNeeExist", "Sadly, no gadget with the given id exists")
            return

        # TODO: Handle update for individual gadgets

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
            ResponseCreator.respond_with_error(req, "GadgetUpdateError",
                                               f"Problem while applying update: {val_str}, {attr_str}")
            return
        ResponseCreator.respond_with_status(req, True)
