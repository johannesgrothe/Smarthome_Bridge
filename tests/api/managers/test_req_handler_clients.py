from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_payload


def test_req_handler_clients_info(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    request_execute_payload(ApiURIs.info_clients.uri,
                            "api_get_all_clients_response",
                            None,
                            {},
                            f_network,
                            f_credentials,
                            f_validator)
