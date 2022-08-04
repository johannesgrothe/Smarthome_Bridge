from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.update.bridge_update_manager import UpdateNotSuccessfulException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_error, request_execute_status


def test_req_handler_system_apply_update(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                         f_credentials, f_update_manager):
    request_execute_status(ApiURIs.bridge_update_execute.uri,
                           {},
                           f_network,
                           f_credentials,
                           f_validator)


def test_req_handler_system_apply_update_validation_error(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager,
                                                          f_credentials, f_update_manager):
    request_execute_error(ApiURIs.bridge_update_execute.uri,
                          "ValidationError",
                          {"yolo": 123},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_system_apply_update_no_updater(f_validator, f_api_manager: ApiManager,
                                                    f_network: DummyNetworkManager,
                                                    f_credentials, f_update_manager):
    f_api_manager.request_handler_bridge._updater = None
    request_execute_error(ApiURIs.bridge_update_execute.uri,
                          "UpdateNotPossibleException",
                          {},
                          f_network,
                          f_credentials,
                          f_validator)


def test_req_handler_system_apply_update_not_successful(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager,
                                                        f_credentials, f_update_manager):
    f_update_manager.mock_exception = UpdateNotSuccessfulException()
    request_execute_error(ApiURIs.bridge_update_execute.uri,
                          "UpdateNotSuccessfulException",
                          {},
                          f_network,
                          f_credentials,
                          f_validator)
