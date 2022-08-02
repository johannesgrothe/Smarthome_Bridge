from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.update.bridge_update_manager import UpdateNotPossibleException, NoUpdateAvailableException, \
    UpdateNotSuccessfulException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager


def test_req_handler_system_echo(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    test_pl = {"test": 123}
    uri = ApiURIs.test_echo.uri
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          test_pl,
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    assert last_response.get_payload() == test_pl


def test_req_handler_system_info(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    uri = ApiURIs.info_bridge.uri
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "api_get_info_response")


def test_req_handler_system_check_update(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                         f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_check.uri

    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "api_bridge_update_check_response")


def test_req_handler_system_check_update_not_available(f_validator, f_api_manager: ApiManager,
                                                       f_network: DummyNetworkManager,
                                                       f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_check.uri
    f_update_manager.mock_exception = NoUpdateAvailableException()
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "default_message")
    assert last_response.get_payload()["ack"] is True


def test_req_handler_system_check_update_validation_error(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager,
                                                          f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_check.uri
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {"yolo": 123},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "ValidationError"


def test_req_handler_system_check_update_not_possible(f_validator, f_api_manager: ApiManager,
                                                      f_network: DummyNetworkManager,
                                                      f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_check.uri
    f_update_manager.mock_exception = UpdateNotPossibleException()
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UpdateNotPossibleException"


def test_req_handler_system_check_update_no_updater(f_validator, f_api_manager: ApiManager,
                                                    f_network: DummyNetworkManager,
                                                    f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_check.uri
    f_api_manager.request_handler_bridge._updater = None
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UpdateNotPossibleException"


def test_req_handler_system_apply_update(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                         f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_execute.uri
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "default_message")
    assert last_response.get_payload()["ack"] is True


def test_req_handler_system_apply_update_validation_error(f_validator, f_api_manager: ApiManager,
                                                          f_network: DummyNetworkManager,
                                                          f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_execute.uri
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {"yolo": 123},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "ValidationError"


def test_req_handler_system_apply_update_no_updater(f_validator, f_api_manager: ApiManager,
                                                    f_network: DummyNetworkManager,
                                                    f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_execute.uri
    f_api_manager.request_handler_bridge._updater = None
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UpdateNotPossibleException"


def test_req_handler_system_apply_update_not_successful(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager,
                                                        f_credentials, f_update_manager):
    uri = ApiURIs.bridge_update_execute.uri
    f_update_manager.mock_exception = UpdateNotSuccessfulException()
    f_network.mock_connector.mock_receive(uri,
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UpdateNotSuccessfulException"
