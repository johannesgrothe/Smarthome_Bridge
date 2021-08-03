import logging
from typing import Optional, Callable

from network.request import Request
from pubsub import Subscriber
from json_validator import Validator, ValidationError

from smarthome_bridge.client_manager import ClientManager, ClientDoesntExistsError, ClientAlreadyExistsError
from smarthome_bridge.network_manager import NetworkManager

from smarthome_bridge.smarthomeclient import SmarthomeClient
from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.gadgets.gadget_factory import GadgetFactory


PATH_HEARTBEAT = "smarthome/heartbeat"
PATH_SYNC = "smarthome/sync"


class ApiManager(Subscriber):

    _logger: logging.Logger
    _validator: Validator
    _clients: ClientManager
    _network: NetworkManager

    def __init__(self, clients: ClientManager, network: NetworkManager):
        self._clients = clients
        self._network = network
        self._network.subscribe(self)
        self._validator = Validator()

    def __del__(self):
        pass

    def receive(self, req: Request):
        self._handle_request(req)

    def _handle_request(self, req: Request):
        self._logger.info(f"Received Request at {req.get_path()}")
        switcher = {
            PATH_HEARTBEAT: self._handle_heartbeat,
            PATH_SYNC: self._handle_sync
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
                self._network.send_request(PATH_SYNC, req.get_sender(), {}, 0)
            else:
                client.trigger_activity()

    def _handle_sync(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_sync_request")
        except ValidationError:
            self._logger.error(f"Request validation error at '{PATH_SYNC}'")

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

        factory = GadgetFactory()
        for gadget in gadgets:
            try:
                gadget_type = GadgetIdentifier(gadget["type"])
            except ValueError:
                self._logger.error(f"Could not create Gadget from type index '{gadget['type']}'")
                continue
            buf_gadget = factory.create_gadget(gadget_type,
                                               gadget["name"],
                                               client_id,
                                               runtime_id,
                                               gadget["characteristics"])

        self._clients.add_client(new_client)