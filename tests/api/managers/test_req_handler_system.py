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
