import pytest

from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.api.exceptions import UnknownClientException
from system.api_definitions import ApiURIs
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import ReqTester


def test_req_handler_clients_request_sync(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                          f_credentials):
    f_api_manager.request_handler_client.request_sync("Test_Client")
    last_sent = f_network.mock_connector.get_last_send_req()
    assert last_sent is not None
    f_validator.validate(last_sent.get_payload(), "api_empty_request")


def test_req_handler_clients_client_reboot(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                           f_client):
    f_api_manager.request_handler_client.send_client_reboot(f_client.id)


def test_req_handler_clients_client_reboot_does_not_exist(f_api_manager: ApiManager, f_network: DummyNetworkManager):
    with pytest.raises(UnknownClientException):
        f_api_manager.request_handler_client.send_client_reboot("spongobob")


def test_req_handler_clients_client_write_system_config(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager,
                                                        f_client):
    f_api_manager.request_handler_client.send_client_system_config_write(f_client.id, {})


def test_req_handler_clients_client_write_system_config_does_not_exist(f_api_manager: ApiManager,
                                                                       f_network: DummyNetworkManager):
    with pytest.raises(UnknownClientException):
        f_api_manager.request_handler_client.send_client_system_config_write("spongobob", {})


def test_req_handler_clients_client_write_gadget_config(f_validator, f_api_manager: ApiManager,
                                                        f_network: DummyNetworkManager,
                                                        f_client):
    f_api_manager.request_handler_client.send_client_gadget_config_write(f_client.id, {})


def test_req_handler_clients_client_write_gadget_config_does_not_exist(f_api_manager: ApiManager,
                                                                       f_network: DummyNetworkManager):
    with pytest.raises(UnknownClientException):
        f_api_manager.request_handler_client.send_client_gadget_config_write("spongobob", {})


def test_req_handler_clients_client_write_event_config(f_validator, f_api_manager: ApiManager,
                                                       f_network: DummyNetworkManager,
                                                       f_client):
    f_api_manager.request_handler_client.send_client_event_config_write(f_client.id, {})


def test_req_handler_clients_client_write_event_config_does_not_exist(f_api_manager: ApiManager,
                                                                      f_network: DummyNetworkManager):
    with pytest.raises(UnknownClientException):
        f_api_manager.request_handler_client.send_client_event_config_write("spongobob", {})


def test_req_handler_clients_info(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.info_clients.uri,
                                         "api_get_all_clients_response",
                                         None,
                                         {})
