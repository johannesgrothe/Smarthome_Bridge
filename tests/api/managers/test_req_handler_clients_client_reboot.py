from clients.client_controller import ClientRebootError
from network.request import NoClientResponseException
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_client_controller import DummyClientController
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_error, request_execute_status


def test_req_handler_clients_client_reboot(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                           f_credentials, f_client):
    request_execute_status(ApiURIs.reboot_connected_client.uri,
                           {"id": f_client.id},
                           f_network,
                           f_credentials,
                           f_validator)


def test_req_handler_clients_client_sync_validation_error(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager,
                                                          f_credentials, f_client):
    request_execute_error(ApiURIs.reboot_connected_client.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_clients_client_reboot_unknown_client(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.reboot_connected_client.uri,
                          "UnknownClientException",
                          {"id": "yolo"},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_clients_client_reboot_no_reboot(f_validator, f_api_manager: ApiManager,
                                                     f_network: DummyNetworkManager, f_credentials, f_client):
    DummyClientController.set_error(NoClientResponseException())
    request_execute_error(ApiURIs.reboot_connected_client.uri,
                          "ClientRebootError",
                          {"id": f_client.id},
                          f_network,
                          f_credentials,
                          f_validator)

    DummyClientController.set_error(ClientRebootError(f_client.id))
    request_execute_error(ApiURIs.reboot_connected_client.uri,
                          "ClientRebootError",
                          {"id": f_client.id},
                          f_network,
                          f_credentials,
                          f_validator)
