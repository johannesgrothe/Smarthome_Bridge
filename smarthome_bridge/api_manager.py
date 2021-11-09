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
from smarthome_bridge.api_params import *
from clients.client_controller import ClientController


class UnknownClientException(Exception):
    def __init__(self, name: str):
        super(UnknownClientException, self).__init__(f"client with name: {name} does nee exist")


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
        self._network.send_request(PATH_SYNC_REQUEST, name, {}, 0)

    def _respond_with_error(self, req: Request, err_type: str, message: str):
        req.respond({"error_type": err_type, "message": message})
        self._logger.error(f"{err_type}: {message}")

    def send_gadget_update(self, gadget: Gadget):
        try:
            gadget_data = ApiEncoder().encode_gadget(gadget)
            self._network.send_broadcast(PATH_SYNC_GADGET,
                                         {"gadget": gadget_data},
                                         0)
        except GadgetEncodeError as err:
            self._logger.error(err.args[0])

    def send_client_reboot(self, client_id: str):
        """
        Triggers the reboot of the specified client

        :param client_id: ID of the client
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.reboot_client()

    def send_client_system_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a system config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_system_config(config)

    def send_client_event_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a event config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_event_config(config)

    def send_client_gadget_config_write(self, client_id: str, config: dict):
        """
        Sends a request to write a gadget config to a client

        :param client_id: ID of the client to send the config to
        :param config: Config to write
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises ConfigWriteError: If client did not acknowledge config writing success
        :raises ValidationError: If passed config was faulty
        """
        if client_id not in [x.get_name() for x in self._delegate.get_client_info()]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_gadget_config(config)

    def _handle_request(self, req: Request):
        self._logger.info(f"Received Request at {req.get_path()}")
        switcher = {
            PATH_HEARTBEAT: self._handle_heartbeat,
            PATH_SYNC_CLIENT: self._handle_client_sync,
            PATH_SYNC_GADGET: self._handle_gadget_sync,
            PATH_INFO_BRIDGE: self._handle_info_bridge,
            PATH_INFO_GADGETS: self._handle_info_gadgets,
            PATH_INFO_CLIENTS: self._handle_info_clients,
            PATH_UPDATE_GADGET: self._handle_update_gadget,
            PATH_CLIENT_REBOOT: self._handle_client_reboot,
            PATH_CLIENT_CONFIG_WRITE: self._handle_client_config_write,
            PATH_CLIENT_CONFIG_DELETE: self._handle_client_config_delete
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), self._handle_unknown)
        handler(req)

    def _handle_unknown(self, req: Request):
        self._logger.error(f"Received request at undefined path '{req.get_path()}'")

    def _handle_heartbeat(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_heartbeat_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_HEARTBEAT}'")
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
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_SYNC_CLIENT}'")
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
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_SYNC_GADGET}'")
            return
        client_id = req.get_sender()

        self._logger.info(f"Syncing gadget from '{client_id}'")
        gadget_data = req.get_payload()["gadget"]
        self._update_gadget(client_id, gadget_data)

    def _handle_info_bridge(self, req: Request):
        data = self._delegate.get_bridge_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_bridge_info(data)
        req.respond(resp_data)

    def _handle_info_gadgets(self, req: Request):
        data = self._delegate.get_gadget_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_all_gadgets_info(data)
        req.respond(resp_data)

    def _handle_info_clients(self, req: Request):
        data = self._delegate.get_client_info()
        encoder = ApiEncoder()
        resp_data = encoder.encode_all_clients_info(data)
        req.respond(resp_data)

    def _handle_update_gadget(self, req: Request):
        """
        Handles a characteristic update request, for a gadget, from any foreign source

        :param req: Request containing the gadget update request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_gadget_update_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_UPDATE_GADGET}'")
            return
        client_id = req.get_sender()

        gadget_info = [x for x in self._delegate.get_gadget_info() if x.get_name() == req.get_payload()["id"]]
        if not gadget_info:
            self._respond_with_error(req, "GagdetDoesNeeExist", "sadly no gagdet with the given id exists")
            return
        encoded_gadget = ApiEncoder().encode_gadget(gadget_info[0])
        for characteristic in req.get_payload()["characteristics"]:
            for characteristic_encoded_gadget in encoded_gadget["characteristics"]:
                if characteristic["type"] == characteristic_encoded_gadget["type"]:
                    characteristic_encoded_gadget["step_value"] = characteristic["step_value"]
                    break

        self._logger.info(f"Updating gadget from '{client_id}'")
        self._update_gadget(gadget_info[0].get_host_client(), encoded_gadget)

    def _handle_client_reboot(self, req: Request):
        """
        Handles a client reboot request

        :param req: Request containing the client id to reboot
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_reboot_request")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_UPDATE_GADGET}'")
            return
        try:
            self.send_client_reboot(req.get_payload()["id"])
        except UnknownClientException:
            self._respond_with_error(req,
                                     "UnknownClientException",
                                     f"nee client with the id: {req.get_payload()['id']} exists")

    def _handle_client_config_write(self, req: Request):
        """
        Handles a client config write request
        :param req: Request containing the client config to write
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_config_write")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_UPDATE_GADGET}'")
            return
        # TODO: handle the request

    def _handle_client_config_delete(self, req: Request):
        """
        Handles a client config delete request
        :param req: Request containing the client config to delete
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_config_delete")
        except ValidationError:
            self._respond_with_error(req, "ValidationError", f"Request validation error at '{PATH_UPDATE_GADGET}'")
            return
        # TODO: handle the request

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
