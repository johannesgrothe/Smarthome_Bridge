from typing import Optional

from network.auth_container import AuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from copy import deepcopy

from utils.json_validator import Validator


def request_execute_error(uri: str, error: str, payload: dict, network: DummyNetworkManager,
                          credentials: Optional[AuthContainer],
                          validator: Validator):
    network.mock_connector.mock_receive(uri,
                                        "testerinski",
                                        payload,
                                        auth=credentials)
    last_response = network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == error


def request_execute_schema(uri: str, schema: str, payload: dict, network: DummyNetworkManager,
                           credentials: Optional[AuthContainer],
                           validator: Validator):
    network.mock_connector.mock_receive(uri,
                                        "testerinski",
                                        payload,
                                        auth=credentials)
    last_response = network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    validator.validate(last_response.get_payload(), schema)


def test_req_handler_configs_get_all(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                     f_credentials):
    request_execute_schema(ApiURIs.config_storage_get_all.uri,
                           "api_config_get_all_response",
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
    request_execute_schema(ApiURIs.config_storage_get.uri,
                           "api_config_get_response",
                           {"config": "Example"},
                           f_network,
                           f_credentials,
                           f_validator)


def test_req_handler_configs_get_config_no_manager(f_validator, f_api_manager: ApiManager,
                                                   f_network: DummyNetworkManager,
                                                   f_credentials):
    f_api_manager.request_handler_configs._configs = None
    request_execute_error(ApiURIs.config_storage_get.uri,
                          "ConfigsNotAvailableError",
                          {"config": "Example"},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_configs_get_config_wrong_name(f_validator, f_api_manager: ApiManager,
                                                   f_network: DummyNetworkManager,
                                                   f_credentials):
    request_execute_error(ApiURIs.config_storage_get.uri,
                          "ConfigDoesNotExistException",
                          {"config": "not_existent"},
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
    uri = ApiURIs.config_storage_save.uri
    test_cfg = deepcopy(f_config_manager.get_config("Example"))
    test_cfg["name"] = "Unittest"
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {"config": test_cfg,
                                           "overwrite": False},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    assert f_config_manager.get_config("Unittest") == test_cfg
    f_validator.validate(last_response.get_payload(), "default_message")
    assert last_response.get_payload()["ack"] is True

    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {"config": test_cfg,
                                           "overwrite": True},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    assert f_config_manager.get_config("Unittest") == test_cfg
    f_validator.validate(last_response.get_payload(), "default_message")
    assert last_response.get_payload()["ack"] is True


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
