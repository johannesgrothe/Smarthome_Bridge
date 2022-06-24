from typing import Callable

from jsonschema.exceptions import ValidationError

from clients.client_controller import ClientRebootError, ClientController
from network.request import Request, NoClientResponseException
from smarthome_bridge.api.exceptions import UnknownClientException
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.api_encoders.client_encoder import ClientApiEncoder
from smarthome_bridge.api_decoders.api_decoder import ApiDecoder, GadgetDecodeError
from smarthome_bridge.client_manager import ClientDoesntExistsError
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.client_status_supplier import ClientStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier
from system.api_definitions import ApiURIs


class RequestHandlerClient(RequestHandler):
    _client_manager: ClientStatusSupplier
    _gadget_manager: GadgetStatusSupplier

    def __init__(self, network: NetworkManager, client_manager: ClientStatusSupplier, gadget_manager: GadgetStatusSupplier):
        super().__init__(network)
        self._client_manager = client_manager
        self._gadget_manager = gadget_manager

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.heartbeat.uri: self._handle_heartbeat,
            ApiURIs.info_clients.uri: self._handle_info_clients,
            ApiURIs.sync_client.uri: self._handle_client_sync,
            ApiURIs.client_config_write.uri: self._handle_client_config_write,
            ApiURIs.client_config_delete.uri: self._handle_client_config_delete
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def request_sync(self, name: str):
        self._logger.info(f"Requesting client sync information from '{name}'")
        self._network.send_request(ApiURIs.sync_request.uri, name, {}, 0)

    def send_client_reboot(self, client_id: str):
        """
        Triggers the reboot of the specified client

        :param client_id: ID of the client
        :return: None
        :raises UnknownClientException: If client id is unknown to the system
        :raises NoClientResponseException: If client did not respond to the request
        :raises ClientRebootError: If client could not be rebooted for aby reason
        """
        if client_id not in [x.id for x in self._client_manager.clients]:
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
        if client_id not in [x.id for x in self._client_manager.clients]:
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
        if client_id not in [x.id for x in self._client_manager.clients]:
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
        if client_id not in [x.id for x in self._client_manager.clients]:
            raise UnknownClientException(client_id)
        writer = ClientController(client_id, self._network)
        writer.write_gadget_config(config)

    def _handle_info_clients(self, req: Request):
        data = self._client_manager.clients
        resp_data = ClientApiEncoder.encode_all_clients_info(data)
        req.respond(resp_data)

    def _handle_heartbeat(self, req: Request):
        try:
            self._validator.validate(req.get_payload(), "bridge_heartbeat_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req,
                                               "ValidationError",
                                               f"Request validation error at '{ApiURIs.heartbeat.uri}'")
            return

        runtime_id = req.get_payload()["runtime_id"]
        client_name = req.get_sender()

        try:
            client = self._client_manager.get_client(client_name)
        except ClientDoesntExistsError:
            self.request_sync(client_name)
            return

        if client.get_runtime_id() != runtime_id:
            self.request_sync(client_name)
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
        except ValidationError as err:
            ResponseCreator.respond_with_error(
                req,
                "ValidationError",
                f"Request validation error at '{ApiURIs.sync_client.uri}': '{err.message}'"
            )
            return

        client_id = req.get_sender()

        self._logger.info(f"Syncing client {client_id}")

        decoder = ApiDecoder()

        new_client = decoder.decode_client(req.get_payload()["client"], req.get_sender())

        gadget_data = req.get_payload()["gadgets"]

        for gadget_info in gadget_data:
            try:
                gadget = ApiDecoder.decode_remote_gadget(gadget_info, client_id)
                self._gadget_manager.add_gadget(gadget)
            except GadgetDecodeError as err:
                print(err.args[0])

        try:
            self._client_manager.remove_client(new_client.id)
        except ClientDoesntExistsError:
            pass
        self._client_manager.add_client(new_client)

    def _handle_client_reboot(self, req: Request):
        """
        Handles a client reboot request

        :param req: Request containing the client id to reboot
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_reboot_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return
        try:
            self.send_client_reboot(req.get_payload()["id"])
        except UnknownClientException:
            ResponseCreator.respond_with_error(req,
                                               "UnknownClientException",
                                               f"Nee client with the id: {req.get_payload()['id']} exists")
        except NoClientResponseException:
            ResponseCreator.respond_with_error(req,
                                               "NoClientResponseException",
                                               f"Client did not respond to reboot request")
        except ClientRebootError:
            ResponseCreator.respond_with_error(req,
                                               "ClientRebootError",
                                               f"Client could not be rebooted for some reason")

    def _handle_client_config_write(self, req: Request):
        """
        Handles a client config write request
        :param req: Request containing the client config to write
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_client_config_write")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.update_gadget.uri}'")
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
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.update_gadget.uri}'")
            return
        # TODO: handle the request
