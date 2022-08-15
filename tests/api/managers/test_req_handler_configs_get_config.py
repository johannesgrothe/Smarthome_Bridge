from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_configs_get_config(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.config_storage_get.uri,
                                         "api_config_get_response",
                                         None,
                                         {"name": "Test"})


def test_req_handler_configs_get_config_no_manager(f_req_tester, f_api_manager: ApiManager):
    f_api_manager.request_handler_configs._configs = None
    f_req_tester.request_execute_error(ApiURIs.config_storage_get.uri,
                                       "ConfigsNotAvailableError",
                                       {"name": "Test"})


def test_req_handler_configs_get_config_wrong_name(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.config_storage_get.uri,
                                       "ConfigDoesNotExistException",
                                       {"name": "not_existent"})


def test_req_handler_configs_get_config_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.config_storage_get.uri,
                                       "ValidationError",
                                       {"test": 1234})
