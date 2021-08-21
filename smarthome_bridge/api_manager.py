import logging
from typing import Optional, Callable
import threading

from network.request import Request
from pubsub import Subscriber
from json_validator import Validator, ValidationError

from logging_interface import LoggingInterface
from smarthome_bridge.client_manager import ClientManager, ClientDoesntExistsError, ClientAlreadyExistsError
from smarthome_bridge.network_manager import NetworkManager

from smarthome_bridge.smarthomeclient import SmarthomeClient
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.gadgets.gadget_factory import GadgetFactory
from smarthome_bridge.gadget_manager import GadgetManager
from smarthome_bridge.gadget_pubsub import GadgetUpdateSubscriber, GadgetUpdatePublisher

from smarthome_bridge.api_encoder import ApiEncoder


PATH_HEARTBEAT = "heartbeat"
PATH_SYNC_CLIENT = "sync/client"
PATH_SYNC_GADGET = "sync/gadget"


class ApiManager(Subscriber, LoggingInterface, GadgetUpdateSubscriber, GadgetUpdatePublisher):

    _validator: Validator
    _clients: ClientManager
    _gadgets: GadgetManager
    _network: NetworkManager

    _gadget_sync_lock: threading.Lock
    _gadget_sync_connection: Optional[str]

    def __init__(self, clients: ClientManager, gadgets: GadgetManager, network: NetworkManager):
        super().__init__()
        self._clients = clients
        self._gadgets = gadgets
        self._network = network
        self._network.subscribe(self)
        self._validator = Validator()
        self._gadget_sync_lock = threading.Lock()
        self._gadget_sync_connection = None

        self._gadgets.subscribe(self)

    def __del__(self):
        pass

    def receive_update(self, gadget: Gadget):
        self._logger.info(f"Forwarding update for {gadget.get_name()}")
        self._handle_gadget_update(gadget)

    def receive(self, req: Request):
        self._handle_request(req)

    def _handle_gadget_update(self, gadget: Gadget):
        gadget_data = ApiEncoder().encode_gadget(gadget)
        self._network.send_request(PATH_SYNC_GADGET,
                                   None,
                                   {"gadget": gadget_data},
                                   0)

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

        client = self._clients.get_client(req.get_sender())
        rt_id = req.get_payload()["runtime_id"]
        if client:
            if client.get_runtime_id() != rt_id:
                self._network.send_request(PATH_SYNC_CLIENT, req.get_sender(), {}, 0)
            else:
                client.trigger_activity()

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

        try:
            self._clients.remove_client(req.get_sender())
        except ClientDoesntExistsError:
            pass

        client_id = req.get_sender()

        self._logger.info(f"Syncing client {client_id}")

        runtime_id = req.get_payload()["runtime_id"]
        port_mapping = req.get_payload()["port_mapping"]
        boot_mode = req.get_payload()["boot_mode"]
        sw_uploaded = req.get_payload()["sw_uploaded"]
        sw_commit = req.get_payload()["sw_commit"]
        sw_branch = req.get_payload()["sw_branch"]

        new_client = SmarthomeClient(name=client_id,
                                     boot_mode=boot_mode,
                                     runtime_id=runtime_id,
                                     flash_date=sw_uploaded,
                                     software_commit=sw_commit,
                                     software_branch=sw_branch,
                                     port_mapping=port_mapping)

        gadgets = req.get_payload()["gadgets"]

        for gadget in gadgets:
            self._update_gadget(client_id, gadget)

        self._clients.add_client(new_client)

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
        client_id = req.get_sender()

        self._logger.info(f"Syncing gadget from {client_id}")
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
        try:
            gadget_type = GadgetIdentifier(gadget_data["type"])
        except ValueError:
            self._logger.error(f"Could not create Gadget from type index '{gadget_data['type']}'")
            return
        factory = GadgetFactory()
        buf_gadget = factory.create_gadget(gadget_type,
                                           gadget_data["name"],
                                           client_id,
                                           gadget_data["characteristics"])

        with self._gadget_sync_lock:
            self._gadgets.receive_update(buf_gadget)
