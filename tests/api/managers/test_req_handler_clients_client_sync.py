from network.auth_container import MqttAuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager


def test_req_handler_clients_client_sync(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                         f_credentials, f_client, f_client_config):
    f_network.mock_connector.mock_receive(ApiURIs.sync_client.uri,
                                          f_client.id,
                                          f_client_config,
                                          auth=MqttAuthContainer())
    last_received = f_network.mock_connector.get_last_send_response()
    assert last_received is None


def test_req_handler_clients_client_sync_does_not_exist(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager,
                                                        f_credentials, f_client, f_client_config, f_clients):
    f_clients.mock_clients = []
    f_network.mock_connector.mock_receive(ApiURIs.sync_client.uri,
                                          f_client.id,
                                          f_client_config,
                                          auth=MqttAuthContainer())
    last_received = f_network.mock_connector.get_last_send_response()
    assert last_received is None


def test_req_handler_clients_client_sync_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.sync_client.uri,
                                       "ValidationError",
                                       {"test": 1234})
