import pytest

from network.auth_container import SerialAuthContainer, MqttAuthContainer, AuthContainer, CredentialsAuthContainer
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs, ApiAccessLevel, ApiEndpointCategory
from system.utils.api_endpoint_definition import ApiEndpointDefinition, ApiAccessType
from test_helpers.dummy_network_connector import DummyNetworkManager

T_PAYLOAD = {"test": 1234}


class BrokenAuthContainer(AuthContainer):
    pass


@pytest.fixture()
def add_uri_not_implemented() -> str:
    ApiURIs.not_implemented = ApiEndpointDefinition("not/implemented",
                                                    [ApiAccessLevel.admin],
                                                    ApiEndpointCategory.System,
                                                    ApiAccessType.read,
                                                    False)
    yield ApiURIs.not_implemented.uri
    del ApiURIs.not_implemented


def test_api_manager_not_implemented(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                     add_uri_not_implemented):
    f_api_manager.auth_manager = None

    f_network.mock_connector.mock_receive(add_uri_not_implemented,
                                          "testerinski",
                                          T_PAYLOAD)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == add_uri_not_implemented
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "NotImplementedError"


def test_api_manager_illegal_uri(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager, f_credentials):
    f_network.mock_connector.mock_receive("yolokoptah",
                                          "testerinski",
                                          {},
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == "yolokoptah"
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UnknownUriError"


def test_api_manager_no_auth(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "NeAuthError"


def test_api_manager_no_auth_manager(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_api_manager.auth_manager = None
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    assert last_response.get_payload() == T_PAYLOAD


def test_api_manager_wrong_direction(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_api_manager.auth_manager = None
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          is_response=True)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is None


def test_api_manager_credentials_auth(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                      f_credentials):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          auth=f_credentials)
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    assert last_response.get_payload() == T_PAYLOAD


def test_api_manager_credentials_auth_bad_pw(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                             f_credentials):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          auth=CredentialsAuthContainer(f_credentials.username, "testpants"))
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "WrongAuthError"


def test_api_manager_credentials_auth_bad_user(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          auth=CredentialsAuthContainer("spongobob", "testpants"))
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UserDoesntExistError"


def test_api_manager_serial_auth(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          auth=SerialAuthContainer())
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    assert last_response.get_payload() == T_PAYLOAD


def test_api_manager_mqtt_auth(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager):
    f_network.mock_connector.mock_receive(ApiURIs.test_echo.uri,
                                          "testerinski",
                                          T_PAYLOAD,
                                          auth=MqttAuthContainer())
    last_response = f_network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "AccessLevelError"


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
