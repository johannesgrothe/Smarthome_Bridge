from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_configs_delete_config(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_status(ApiURIs.config_storage_delete.uri,
                                        {"name": "Test"})


def test_req_handler_configs_delete_config_does_not_exist(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.config_storage_delete.uri,
                                       "ConfigDoesNotExistException",
                                       {"name": "does_not_exist"})


def test_req_handler_configs_delete_config_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.config_storage_delete.uri,
                                       "ValidationError",
                                       {"test": 1234})


def test_req_handler_configs_delete_config_no_manager(f_req_tester, f_api_manager: ApiManager):
    f_api_manager.request_handler_configs._configs = None
    f_req_tester.request_execute_error(ApiURIs.config_storage_delete.uri,
                                       "ConfigsNotAvailableError",
                                       {"name": "Test"})
