from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from copy import deepcopy

from tests.api.managers.api_test_templates import request_execute_payload, request_execute_error, request_execute_status


def test_req_handler_configs_get_all(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                     f_credentials):
    request_execute_payload(ApiURIs.config_storage_get_all.uri,
                            "api_config_get_all_response",
                            None,
                            {},
                            f_network,
                            f_credentials,
                            f_validator)


def test_req_handler_configs_get_all_no_manager(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                                f_credentials):
    f_api_manager.request_handler_configs._configs = None
    request_execute_error(ApiURIs.config_storage_get_all.uri,
                          "ConfigsNotAvailableError",
                          {},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_get_all_validation_error(f_validator, f_api_manager: ApiManager,
                                                      f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.config_storage_get_all.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_get_config(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                        f_credentials):
    request_execute_payload(ApiURIs.config_storage_get.uri,
                            "api_config_get_response",
                            None,
                            {"name": "Test"},
                            f_network,
                            f_credentials,
                            f_validator)


def test_req_handler_configs_get_config_no_manager(f_validator, f_api_manager: ApiManager,
                                                   f_network: DummyNetworkManager,
                                                   f_credentials):
    f_api_manager.request_handler_configs._configs = None
    request_execute_error(ApiURIs.config_storage_get.uri,
                          "ConfigsNotAvailableError",
                          {"name": "Test"},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_get_config_wrong_name(f_validator, f_api_manager: ApiManager,
                                                   f_network: DummyNetworkManager,
                                                   f_credentials):
    request_execute_error(ApiURIs.config_storage_get.uri,
                          "ConfigDoesNotExistException",
                          {"name": "not_existent"},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_get_config_validation_error(f_validator, f_api_manager: ApiManager,
                                                         f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.config_storage_get.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_add_config(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                        f_credentials, f_config_manager):
    test_cfg = deepcopy(f_config_manager.get_config("Example"))
    test_cfg["name"] = "Unittest"

    request_execute_status(ApiURIs.config_storage_save.uri,
                           {"config": test_cfg,
                            "overwrite": False},
                           f_network,
                           f_credentials,
                           f_validator)
    assert f_config_manager.get_config("Unittest") == test_cfg

    request_execute_status(ApiURIs.config_storage_save.uri,
                           {"config": test_cfg,
                            "overwrite": True},
                           f_network,
                           f_credentials,
                           f_validator)
    assert f_config_manager.get_config("Unittest") == test_cfg


def test_req_handler_configs_add_config_already_exists(f_validator, f_api_manager: ApiManager,
                                                       f_network: DummyNetworkManager,
                                                       f_credentials, f_config_manager):
    test_cfg = deepcopy(f_config_manager.get_config("Example"))
    test_cfg["name"] = "Unittest"
    f_config_manager.write_config(test_cfg)

    request_execute_error(ApiURIs.config_storage_save.uri,
                          "ConfigAlreadyExistsException",
                          {"config": test_cfg,
                           "overwrite": False},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_add_config_no_manager(f_validator, f_api_manager: ApiManager,
                                                   f_network: DummyNetworkManager, f_credentials, f_config_manager):
    test_cfg = f_config_manager.get_config("Example")
    test_cfg["name"] = "Unittest"
    f_api_manager.request_handler_configs._configs = None

    request_execute_error(ApiURIs.config_storage_save.uri,
                          "ConfigsNotAvailableError",
                          {"config": test_cfg,
                           "overwrite": False},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_add_config_validation_error(f_validator, f_api_manager: ApiManager,
                                                         f_network: DummyNetworkManager, f_credentials):
    request_execute_error(ApiURIs.config_storage_save.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_delete_config(f_validator, f_api_manager: ApiManager,
                                           f_network: DummyNetworkManager, f_credentials):
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
