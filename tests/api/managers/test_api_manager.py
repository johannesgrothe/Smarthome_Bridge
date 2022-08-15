import pytest

from network.auth_container import SerialAuthContainer, MqttAuthContainer, AuthContainer, CredentialsAuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.api.request_handler_bridge import RequestHandlerBridge
from smarthome_bridge.api.request_handler_client import RequestHandlerClient
from smarthome_bridge.api.request_handler_configs import RequestHandlerConfigs
from smarthome_bridge.api.request_handler_gadget import RequestHandlerGadget
from system.api_definitions import ApiURIs, ApiAccessLevel, ApiEndpointCategory
from system.utils.api_endpoint_definition import ApiEndpointDefinition, ApiAccessType
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import ReqTester

T_PAYLOAD = {"test": 1234}
T_PAYLOAD_LONG = {f"test_{x}": x ** 2 for x in range(1, 5)}


class BrokenAuthContainer(AuthContainer):
    pass


@pytest.fixture()
def add_uri_not_implemented() -> str:
    ApiURIs.not_implemented = ApiEndpointDefinition("not/implemented",
                                                    [ApiAccessLevel.admin],
                                                    ApiEndpointCategory.System,
                                                    ApiAccessType.read,
                                                    False,
                                                    True)
    yield ApiURIs.not_implemented.uri
    del ApiURIs.not_implemented


def test_api_manager_getters(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                             add_uri_not_implemented):
    assert isinstance(f_api_manager.request_handler_bridge, RequestHandlerBridge)
    assert isinstance(f_api_manager.request_handler_client, RequestHandlerClient)
    assert isinstance(f_api_manager.request_handler_gadget, RequestHandlerGadget)
    assert isinstance(f_api_manager.request_handler_configs, RequestHandlerConfigs)


def test_api_manager_not_implemented(f_req_tester, f_api_manager: ApiManager, add_uri_not_implemented):
    f_api_manager.auth_manager = None
    f_req_tester.request_execute_error(add_uri_not_implemented,
                                       "NotImplementedError",
                                       T_PAYLOAD)


def test_api_manager_illegal_uri(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error("yolokoptah",
                                       "UnknownUriError",
                                       {})


def test_api_manager_no_auth(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.credentials = None
    f_req_tester.request_execute_error(ApiURIs.test_echo.uri,
                                       "NeAuthError",
                                       T_PAYLOAD)


def test_api_manager_no_auth_manager(f_req_tester, f_api_manager: ApiManager):
    f_api_manager.auth_manager = None
    f_req_tester.credentials = None
    f_req_tester.request_execute_payload(ApiURIs.test_echo.uri,
                                         None,
                                         T_PAYLOAD,
                                         T_PAYLOAD)


def test_api_manager_wrong_direction(f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_api_manager.auth_manager = None
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          is_response=True)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is None


def test_api_manager_credentials_auth(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.test_echo.uri,
                                         None,
                                         T_PAYLOAD_LONG,
                                         T_PAYLOAD_LONG)


def test_api_manager_credentials_auth_bad_pw(f_req_tester, f_api_manager: ApiManager, f_credentials):
    f_req_tester.credentials = CredentialsAuthContainer(f_credentials.username, "testpants")
    f_req_tester.request_execute_error(ApiURIs.test_echo.uri,
                                       "WrongAuthError",
                                       T_PAYLOAD)


def test_api_manager_credentials_auth_bad_user(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.credentials = CredentialsAuthContainer("spongobob", "testpants")
    f_req_tester.request_execute_error(ApiURIs.test_echo.uri,
                                       "UserDoesntExistError",
                                       T_PAYLOAD)


def test_api_manager_serial_auth(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.credentials = SerialAuthContainer()
    f_req_tester.request_execute_payload(ApiURIs.test_echo.uri,
                                         None,
                                         T_PAYLOAD,
                                         T_PAYLOAD)


def test_api_manager_mqtt_auth(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.credentials = MqttAuthContainer()
    f_req_tester.request_execute_error(ApiURIs.test_echo.uri,
                                       "AccessLevelError",
                                       T_PAYLOAD)


def test_api_manager_broken_auth(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    with pytest.raises(TypeError):
        f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                              "testerinski",
                                              T_PAYLOAD,
                                              auth=BrokenAuthContainer())


def test_api_manager_response(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_network.mock_connector.mock_receive(ApiURIs.sync_request.uri,
                                          "testerinski",
                                          {},
                                          is_response=True)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is None
