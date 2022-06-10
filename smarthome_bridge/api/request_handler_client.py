from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler


class RequestHandlerClient(RequestHandler):
    def handle_request(self, req: Request) -> None:
        pass

    def _handle_heartbeat(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_heartbeat_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{ApiURIs.heartbeat.uri}'")
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
                                     f"Request validation error at '{ApiURIs.sync_client.uri}': '{err.message}'")
            return

        client_id = req.get_sender()

        self._logger.info(f"Syncing client {client_id}")

        decoder = ApiDecoder()

        new_client = decoder.decode_client(req.get_payload()["client"], req.get_sender())

        gadget_data = req.get_payload()["gadgets"]

        for gadget in gadget_data:
            self._handle_gadget(client_id, gadget)

        self._delegate.handle_client_sync(new_client)
