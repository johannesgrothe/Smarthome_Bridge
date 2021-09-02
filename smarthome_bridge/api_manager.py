from typing import Optional, Callable

from network.request import Request
from pubsub import Subscriber
from json_validator import Validator, ValidationError

from logging_interface import LoggingInterface
from smarthome_bridge.network_manager import NetworkManager

from gadgets.gadget import Gadget

from smarthome_bridge.api_encoder import ApiEncoder, GadgetEncodeError
from smarthome_bridge.api_decoder import ApiDecoder, GadgetDecodeError, ClientDecodeError
from smarthome_bridge.api_manager_delegate import ApiManagerDelegate


PATH_HEARTBEAT = "heartbeat"
PATH_SYNC_CLIENT = "sync/client"
PATH_SYNC_GADGET = "sync/gadget"


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
        self._network.send_request(PATH_SYNC_CLIENT, name, {}, 0)

    def send_gadget_update(self, gadget: Gadget):
        try:
            gadget_data = ApiEncoder().encode_gadget(gadget)
            self._network.send_broadcast(PATH_SYNC_GADGET,
                                         {"gadget": gadget_data},
                                         0)
        except GadgetEncodeError as err:
            self._logger.error(err.args[0])

    def _handle_request(self, req: Request):
        self._logger.info(f"Received Request at {req.get_path()}")
        switcher = {
            PATH_HEARTBEAT: self._handle_heartbeat,
            PATH_SYNC_CLIENT: self._handle_client_sync,
            PATH_SYNC_GADGET: self._handle_gadget_sync
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), self._handle_unknown)
        handler(req)

    def _handle_unknown(self, req: Request):
        self._logger.error(f"Received request at undefined path '{req.get_path()}'")

    def _handle_heartbeat(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_heartbeat_request")
        except ValidationError:
            self._logger.error(f"Request validation error at '{PATH_HEARTBEAT}'")
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
        except ValidationError:
            self._logger.error(f"Request validation error at '{PATH_SYNC_CLIENT}'")
            return

        client_id = req.get_sender()

        self._logger.info(f"Syncing client {client_id}")

        decoder = ApiDecoder()

        new_client = decoder.decode_client(req.get_payload()["client"], req.get_sender())

        gadget_data = req.get_payload()["gadgets"]

        for gadget in gadget_data:
            self._update_gadget(client_id, gadget)

        self._delegate.handle_client_update(new_client)

    def _handle_gadget_sync(self, req: Request):
        """
        Handles a gadget update request from any foreign source

        :param req: Request containing the gadget update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_gadget_sync_request")
        except ValidationError:
            self._logger.error(f"Request validation error at '{PATH_SYNC_GADGET}'")
            return
        client_id = req.get_sender()

        self._logger.info(f"Syncing gadget from '{client_id}'")
        gadget_data = req.get_payload()["gadget"]
        self._update_gadget(client_id, gadget_data)

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
            self._delegate.handle_gadget_update(buf_gadget)

        except GadgetDecodeError as err:
            self._logger.error(err.args[0])
            return
