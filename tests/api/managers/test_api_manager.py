import datetime
import pytest

from network.auth_container import CredentialsAuthContainer
from smarthome_bridge.api.api_manager import ApiManager, ApiManagerSetupContainer
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.network_manager import NetworkManager
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from system.api_definitions import ApiURIs, ApiAccessLevel
from test_helpers.dummy_network_connector import DummyNetworkConnector
from test_helpers.dummy_status_suppliers import DummyGadgetStatusSupplier, DummyClientStatusSupplier, \
    DummyBridgeStatusSupplier, DummyGadgetPublisherStatusSupplier
from utils.auth_manager import AuthManager
from utils.user_manager import UserManager



def test_api_manager_illegal_uri(f_validator, f_api_manager: ApiManager, f_network: NetworkManager):
    network.mock_receive("yolokoptah",
                         "testerinski",
                         {},
                         auth=CredentialsAuthContainer(USER_NAME, USER_PW))
    last_response = network.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == "yolokoptah"
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "UnknownUriError"


def test_api_manager_no_auth(f_validator, api_manager: ApiManager, network: DummyNetworkConnector):
    network.mock_receive(ApiURIs.test_echo.uri,
                         "testerinski",
                         {"test": 123})
    last_response = network.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    f_validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == "NeAuthError"
