from typing import Callable

from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api_coders.gadget_publisher_api_encoder import GadgetPublisherApiEncoder
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from system.api_definitions import ApiURIs


class RequestHandlerGadgetPublisher(RequestHandler):
    _status_supplier: GadgetPublisherStatusSupplier

    def __init__(self, network: NetworkManager, supplier: GadgetPublisherStatusSupplier):
        super().__init__(network)
        self._status_supplier = supplier

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.info_gadget_publishers: self._handle_info_gadget_publishers
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def _handle_info_gadget_publishers(self, req: Request):
        data = self._status_supplier.publishers
        resp_data = GadgetPublisherApiEncoder.encode_gadget_publisher_list(data)
        req.respond(resp_data)
