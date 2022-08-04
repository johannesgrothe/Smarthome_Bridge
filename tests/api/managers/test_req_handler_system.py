from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.update.bridge_update_manager import UpdateNotPossibleException, NoUpdateAvailableException, \
    UpdateNotSuccessfulException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_payload


def test_req_handler_system_echo(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    test_pl = {"test": 123}
    request_execute_payload(ApiURIs.test_echo.uri,
                            None,
                            test_pl,
                            test_pl,
                            f_network,
                            f_credentials,
                            f_validator)


def test_req_handler_system_info(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    request_execute_payload(ApiURIs.info_bridge.uri,
                            "api_get_info_response",
                            None,
                            {},
                            f_network,
                            f_credentials,
                            f_validator)
