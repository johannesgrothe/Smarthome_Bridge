import datetime
import os
from typing import Optional, List

import pytest

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from network.auth_container import AuthContainer, CredentialsAuthContainer
from network.request import Request
from smarthome_bridge.api.api_manager import ApiManager, ApiManagerSetupContainer
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.client import Client
from smarthome_bridge.status_supplier_interfaces.bridge_status_supplier import BridgeStatusSupplier
from smarthome_bridge.status_supplier_interfaces.client_status_supplier import ClientStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_publisher_status_supplier import GadgetPublisherStatusSupplier
from smarthome_bridge.status_supplier_interfaces.gadget_status_supplier import GadgetStatusSupplier
from system.api_definitions import ApiURIs, ApiAccessLevel
from test_helpers.dummy_network_connector import DummyNetworkConnector
from utils.auth_manager import AuthManager
from utils.user_manager import UserManager

HOSTNAME = "unittest_host"
T_LAUCH = datetime.datetime.now()
USER_NAME = "testadmin"
USER_PW = "testpw"


class DummyGadgetStatusSupplier(GadgetStatusSupplier):
    mock_gadgets: list[Gadget]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_gadgets = []

    def get_gadget(self, gadget_id: str) -> Optional[Gadget]:
        for gadget in self.mock_gadgets:
            if gadget.id == gadget_id:
                return gadget
        return None

    def add_gadget(self, gadget: Gadget):
        self.mock_gadgets.append(gadget)

    def _get_gadgets(self) -> list[Gadget]:
        return self.mock_gadgets


class DummyClientStatusSupplier(ClientStatusSupplier):
    mock_clients: list[Client]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_clients = []

    def _get_clients(self) -> list[Client]:
        return self.mock_clients

    def add_client(self, client: Client) -> None:
        self.mock_clients.append(client)

    def remove_client(self, client_id: str) -> None:
        found = None
        for client in self.mock_clients:
            if client.id == client_id:
                found = client
        self.mock_clients.remove(found)

    def get_client(self, client_id: str) -> Optional[Client]:
        for client in self.mock_clients:
            if client.id == client_id:
                return client
        return None


class DummyBridgeStatusSupplier(BridgeStatusSupplier):

    def __init__(self, info: BridgeInformationContainer):
        super().__init__()
        self.mock_info = info

    def _get_info(self) -> BridgeInformationContainer:
        return self.mock_info


class DummyGadgetPublisher(GadgetPublisher):
    mock_last_update: Optional[GadgetUpdateContainer]
    mock_add_gadget: Optional[str]
    mock_remove_gadget: Optional[str]

    def __init__(self):
        super().__init__()
        self.reset()

    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        self.mock_last_update = update_container

    def add_gadget(self, gadget_id: str):
        self.mock_add_gadget = gadget_id

    def remove_gadget(self, gadget_id: str):
        self.mock_remove_gadget = gadget_id

    def reset(self):
        self.mock_last_update = None
        self.mock_add_gadget = None
        self.mock_remove_gadget = None


class DummyGadgetPublisherStatusSupplier(GadgetPublisherStatusSupplier):
    mock_publishers: list[GadgetPublisher]

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.mock_publishers = []

    def _get_publishers(self) -> List[GadgetPublisher]:
        return self.mock_publishers


@pytest.fixture()
def gadgets() -> DummyGadgetStatusSupplier:
    return DummyGadgetStatusSupplier()


@pytest.fixture()
def clients() -> DummyClientStatusSupplier:
    return DummyClientStatusSupplier()


@pytest.fixture()
def bridge() -> DummyBridgeStatusSupplier:
    info = BridgeInformationContainer("dummy_bridge",
                                      "test_branch",
                                      "abcdef123456789",
                                      T_LAUCH,
                                      "1.1.1",
                                      "2.2.2",
                                      "3.3.3",
                                      "4.4.4")
    return DummyBridgeStatusSupplier(info)


@pytest.fixture()
def publishers() -> GadgetPublisherStatusSupplier:
    return DummyGadgetPublisherStatusSupplier()


@pytest.fixture()
def auth(f_temp_exists) -> AuthManager:
    auth = AuthManager(UserManager(f_temp_exists))
    auth.users.add_user(USER_NAME, USER_PW, ApiAccessLevel.admin, persistent_user=False)
    return auth


@pytest.fixture()
def network() -> DummyNetworkConnector:
    network = DummyNetworkConnector(HOSTNAME)
    yield network
    network.__del__()


@pytest.fixture()
def setup_data(network, gadgets, clients, bridge, publishers, auth) -> ApiManagerSetupContainer:
    return ApiManagerSetupContainer(network,
                                    gadgets,
                                    clients,
                                    publishers,
                                    bridge,
                                    auth)


@pytest.fixture
def api_manager(setup_data) -> ApiManager:
    manager = ApiManager(setup_data)
    yield manager
    manager.__del__()


def test_api_manager_illegal_uri(f_validator, api_manager: ApiManager, network: DummyNetworkConnector):
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


def test_api_manager_echo(f_validator, api_manager: ApiManager, network: DummyNetworkConnector):
    test_pl = {"test": 123}
    network.mock_receive(ApiURIs.test_echo.uri,
                         "testerinski",
                         test_pl,
                         auth=CredentialsAuthContainer(USER_NAME, USER_PW))
    last_response = network.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == ApiURIs.test_echo.uri
    assert last_response.get_payload() == test_pl
