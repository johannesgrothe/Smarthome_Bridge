from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from copy import deepcopy


def test_req_handler_configs_add_config(f_req_tester, f_api_manager: ApiManager, f_config_manager):
    test_cfg = deepcopy(f_config_manager.get_config("Example"))
    test_cfg["name"] = "Unittest"

    f_req_tester.request_execute_status(ApiURIs.config_storage_save.uri,
                                        {"config": test_cfg,
                                         "overwrite": False})
    assert f_config_manager.get_config("Unittest") == test_cfg

    f_req_tester.request_execute_status(ApiURIs.config_storage_save.uri,
                                        {"config": test_cfg,
                                         "overwrite": True})
    assert f_config_manager.get_config("Unittest") == test_cfg


def test_req_handler_configs_add_config_already_exists(f_req_tester, f_api_manager: ApiManager, f_config_manager):
    test_cfg = deepcopy(f_config_manager.get_config("Example"))
    test_cfg["name"] = "Unittest"
    f_config_manager.write_config(test_cfg)

    f_req_tester.request_execute_error(ApiURIs.config_storage_save.uri,
                                       "ConfigAlreadyExistsException",
                                       {"config": test_cfg,
                                        "overwrite": False})


def test_req_handler_configs_add_config_no_manager(f_req_tester, f_api_manager: ApiManager, f_config_manager):
    test_cfg = f_config_manager.get_config("Example")
    test_cfg["name"] = "Unittest"
    f_api_manager.request_handler_configs._configs = None

    f_req_tester.request_execute_error(ApiURIs.config_storage_save.uri,
                                       "ConfigsNotAvailableError",
                                       {"config": test_cfg,
                                        "overwrite": False})


def test_req_handler_configs_add_config_validation_error(f_req_tester, f_api_manager: ApiManager, f_credentials):
    f_req_tester.request_execute_error(ApiURIs.config_storage_save.uri,
                                       "ValidationError",
                                       {"test": 1234})
