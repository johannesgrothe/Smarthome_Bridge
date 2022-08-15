from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_configs_get_all(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.config_storage_get_all.uri,
                                         "api_config_get_all_response",
                                         None,
                                         {})


def test_req_handler_configs_get_all_no_manager(f_req_tester, f_api_manager: ApiManager):
    f_api_manager.request_handler_configs._configs = None
    f_req_tester.request_execute_error(ApiURIs.config_storage_get_all.uri,
                                       "ConfigsNotAvailableError",
                                       {})


def test_req_handler_configs_get_all_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.config_storage_get_all.uri,
                                       "ValidationError",
                                       {"test": 1234})
