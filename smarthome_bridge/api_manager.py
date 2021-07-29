import logging
from typing import Optional, Callable

from network.request import Request
from pubsub import Subscriber
from json_validator import Validator, ValidationError

from smarthome_bridge.client_manager import ClientManager
from smarthome_bridge.network_manager import NetworkManager

from smarthome_bridge.smarthomeclient import SmarthomeClient


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
                client.update_runtime_id(rt_id)
                self._network.send_request(PATH_SYNC, req.get_sender(), {}, 0)
        else:
            client = SmarthomeClient(req.get_sender(), rt_id)
            self._network.send_request(PATH_SYNC, req.get_sender(), {}, 0)

        client.trigger_activity()

    def _handle_sync(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_sync_request")
        except ValidationError:
            self._logger.error(f"Request validation error at '{PATH_SYNC}'")

        client = self._clients.get_client(req.get_sender())
        rt_id = req.get_payload()["runtime_id"]
        if client and client.get_runtime_id() == rt_id:
            client.update_data()