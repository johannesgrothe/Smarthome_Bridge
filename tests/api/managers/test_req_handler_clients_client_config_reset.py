from clients.client_controller import ConfigEraseError
from network.request import NoClientResponseException
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_client_controller import DummyClientController


def test_req_handler_clients_client_config_delete(f_req_tester, f_api_manager: ApiManager, f_client):
    f_req_tester.request_execute_status(ApiURIs.client_config_delete.uri,
                                        {"id": f_client.id})


def test_req_handler_clients_client_config_delete_validation_error(f_req_tester, f_api_manager: ApiManager, f_client):
    f_req_tester.request_execute_error(ApiURIs.client_config_delete.uri,
                                       "ValidationError",
                                       {"test": 1234})


def test_req_handler_clients_client_config_delete_unknown_client(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.client_config_delete.uri,
                                       "UnknownClientException",
                                       {"id": "yolo"})


def test_req_handler_clients_client_reboot_failed(f_req_tester, f_api_manager: ApiManager, f_client):
    DummyClientController.set_error(ConfigEraseError(f_client.id))
    f_req_tester.request_execute_error(ApiURIs.client_config_delete.uri,
                                       "ConfigDeleteError",
                                       {"id": f_client.id})

    DummyClientController.set_error(NoClientResponseException())
    f_req_tester.request_execute_error(ApiURIs.client_config_delete.uri,
                                       "ConfigDeleteError",
                                       {"id": f_client.id})
