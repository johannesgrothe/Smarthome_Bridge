from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager


def test_req_handler_system_echo(f_req_tester, f_api_manager: ApiManager):
    test_pl = {"test": 123}
    f_req_tester.request_execute_payload(ApiURIs.test_echo.uri,
                                         None,
                                         test_pl,
                                         test_pl)


def test_req_handler_system_info(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.info_bridge.uri,
                                         "api_get_info_response",
                                         None,
                                         {})
