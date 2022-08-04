import pytest

from clients.client_controller import ClientRebootError
from network.request import NoClientResponseException
from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.api.exceptions import UnknownClientException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_payload


def test_req_handler_clients_request_sync(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                          f_credentials):
    f_api_manager.request_handler_client.request_sync("Test_Client")
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is not None
    f_validator.validate(last_sent.get_payload(), "api_empty_request")


def test_req_handler_clients_client_reboot(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                           f_client):
    f_network.mock_connector.mock_ack(True)
    f_api_manager.request_handler_client.send_client_reboot(f_client.id)
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is not None
    f_validator.validate(last_sent.get_payload(), "client_api_system_request")
    assert last_sent.get_payload() == {"subject": "reboot"}


def test_req_handler_clients_client_reboot_does_not_exist(f_api_manager: ApiManager, f_network: DummyNetworkManager):
    with pytest.raises(UnknownClientException):
        f_api_manager.request_handler_client.send_client_reboot("spongobob")
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is None


def test_req_handler_clients_client_reboot_no_response(f_validator, f_api_manager: ApiManager,
                                                       f_network: DummyNetworkManager, f_client):
    with pytest.raises(NoClientResponseException):
        f_api_manager.request_handler_client.send_client_reboot(f_client.id)
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is not None
    f_validator.validate(last_sent.get_payload(), "client_api_system_request")
    assert last_sent.get_payload() == {"subject": "reboot"}


def test_req_handler_clients_client_reboot_no_ack(f_validator, f_api_manager: ApiManager,
                                                  f_network: DummyNetworkManager, f_client):
    f_network.mock_connector.mock_ack(False)
    with pytest.raises(ClientRebootError):
        f_api_manager.request_handler_client.send_client_reboot(f_client.id)
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is not None
    f_validator.validate(last_sent.get_payload(), "client_api_system_request")
    assert last_sent.get_payload() == {"subject": "reboot"}


def test_req_handler_clients_info(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                  f_credentials):
    request_execute_payload(ApiURIs.info_clients.uri,
                            "api_get_all_clients_response",
                            None,
                            {},
                            f_network,
                            f_credentials,
                            f_validator)
