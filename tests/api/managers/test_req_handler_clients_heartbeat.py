import pytest

from network.auth_container import MqttAuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.api.exceptions import UnknownClientException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_payload, request_execute_error


def test_req_handler_clients_heartbeat(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                       f_credentials, f_client):
    f_network.mock_connector.mock_receive(ApiURIs.heartbeat.uri,
                                          f_client.id,
                                          {"runtime_id": f_client.runtime_id},
                                          auth=MqttAuthContainer())
    assert f_network.mock_connector.get_last_send_response() is None


def test_req_handler_clients_heartbeat_validation_error(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager):
    request_execute_error(ApiURIs.heartbeat.uri,
                          "ValidationError",
                          {"test": 1234},
                          f_network,
                          MqttAuthContainer(),
                          f_validator)


def test_req_handler_clients_heartbeat_does_not_exist(f_validator, f_api_manager: ApiManager,
                                                      f_network: DummyNetworkManager,
                                                      f_credentials):
    f_network.mock_connector.mock_receive(ApiURIs.heartbeat.uri,
                                          "spongobob",
                                          {"runtime_id": 12345677},
                                          auth=MqttAuthContainer())
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is None

    last_request = f_network.mock_connector.get_last_send_req()
    assert last_request is not None
    f_validator.validate(last_request.get_payload(), "api_empty_request")


def test_req_handler_clients_heartbeat_outdated_runtime_id(f_validator, f_api_manager: ApiManager,
                                                           f_network: DummyNetworkManager,
                                                           f_credentials, f_client):
    f_network.mock_connector.mock_receive(ApiURIs.heartbeat.uri,
                                          f_client.id,
                                          {"runtime_id": 12345677},
                                          auth=MqttAuthContainer())
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is None

    last_request = f_network.mock_connector.get_last_send_req()
    assert last_request is not None
    f_validator.validate(last_request.get_payload(), "api_empty_request")
