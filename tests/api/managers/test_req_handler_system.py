from network.auth_container import CredentialsAuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.api.request_handler_bridge import RequestHandlerBridge
from smarthome_bridge.network_manager import NetworkManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkConnector

from tests.api.managers.test_api_manager import api_manager, network, USER_NAME, USER_PW


def test_api_manager_echo(f_validator, api_manager: ApiManager, network: NetworkManager):
    test_pl = {"test": 123}
    uri = ApiURIs.info_gadgets.uri
    network.mock_receive(uri,
                         "testerinski",
                         test_pl,
                         auth=CredentialsAuthContainer(USER_NAME, USER_PW))
    last_response = network.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    assert last_response.get_payload() == test_pl
