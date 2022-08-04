from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager

from tests.api.managers.api_test_templates import request_execute_error, request_execute_status


def test_req_handler_configs_delete_config(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                           f_credentials):
    request_execute_status(ApiURIs.config_storage_delete.uri,
                           {"name": "Test"},
                           f_network,
                           f_credentials,
                           f_validator)


def test_req_handler_configs_delete_config_does_not_exist(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.config_storage_delete.uri,
                          "ConfigDoesNotExistException",
                          {"name": "does_not_exist"},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_delete_config_validation_error(f_validator, f_api_manager: ApiManager,
                                                            f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.config_storage_delete.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_delete_config_no_manager(f_validator, f_api_manager: ApiManager,
                                                      f_network: DummyNetworkManager, f_credentials):
    f_api_manager.request_handler_configs._configs = None
    request_execute_error(ApiURIs.config_storage_delete.uri,
                          "ConfigsNotAvailableError",
                          {"name": "Test"},
                          f_network,
                          f_credentials,
                          f_validator)
