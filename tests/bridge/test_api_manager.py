import datetime

import pytest

from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.network_manager import NetworkManager
from test_helpers.dummy_api_delegate import DummyApiDelegate
from network.request import Request, NoResponsePossibleException
from test_helpers.dummy_network_connector import DummyNetworkConnector
from gadgets.fan_westinghouse_ir import FanWestinghouseIR
from smarthome_bridge.client import Client
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from gadgets.gadget import Gadget

HOSTNAME = "unittest_host"
REQ_SENDER = "unittest"
REQ_RUNTIME = 123456

GADGET_NAME = "test_fan"
GADGET_CHARACTERISTIC_TYPE = 1
CLIENT_NAME = "test_client"

GADGET_CONFIG_OK = {
    "gadget": {
        "type": 3,
        "name": GADGET_NAME,
        "characteristics": [{
            "type": 1,
            "min": 0,
            "max": 1,
            "steps": 1,
            "step_value": 1,
            "true_value": 1,
            "percentage_value": 100
        }, {
            "type": 2,
            "min": 0,
            "max": 100,
            "steps": 4,
            "step_value": 4,
            "true_value": 100,
            "percentage_value": 100
        }]
    }
}

GADGET_CHARACTERISTICS = [{
        "type": 1,
            "min": 0,
            "max": 1,
            "steps": 1,
            "step_value": 1,
            "true_value": 1,
            "percentage_value": 100
        }, {
            "type": 2,
            "min": 0,
            "max": 100,
            "steps": 4,
            "step_value": 4,
            "true_value": 100,
            "percentage_value": 100
}]


GADGET_CONFIG_ERR = {
    "type": 55,
    "name": GADGET_NAME,
    "characteristics": [{
        "type": 1,
        "min": 0,
        "max": 1,
        "steps": 1,
        "step_value": 1,
        "true_value": 1,
        "percentage_value": 100
    }]
}

GADGET_UPDATE_ERR = {
    "id": GADGET_NAME,
    "characteristics": [{
        "type": GADGET_CHARACTERISTIC_TYPE,
    }]
}

GADGET_UPDATE_ERR_UNKNOWN = {
    "id": "blubb",
    "characteristics": [{
        "type": GADGET_CHARACTERISTIC_TYPE,
        "step_value": 0
    }]
}

GADGET_UPDATE_OK = {
    "id": GADGET_NAME,
    "characteristics": [{
        "type": GADGET_CHARACTERISTIC_TYPE,
        "step_value": 0
    }]
}

CLIENT_CONFIG_OK = {
    "client": {
        "runtime_id": REQ_RUNTIME,
        "port_mapping": {},
        "boot_mode": 1,
        "sw_uploaded": None,
        "sw_commit": None,
        "sw_branch": None
    },
    "gadgets": [
        GADGET_CONFIG_OK["gadget"]
    ]
}


@pytest.fixture()
def gadget():
    gadget = FanWestinghouseIR(GADGET_NAME,
                               CLIENT_NAME,
                               Characteristic(CharacteristicIdentifier.status,
                                              0,
                                              1),
                               Characteristic(CharacteristicIdentifier.fanSpeed,
                                              0,
                                              100,
                                              4))
    yield gadget
    gadget.__del__()


@pytest.fixture()
def client():
    client = Client(CLIENT_NAME,
                    1773,
                    datetime.datetime.now(),
                    None,
                    None,
                    {},
                    1)
    yield client


@pytest.fixture()
def delegate(gadget, client):
    delegate = DummyApiDelegate()
    delegate.add_gadget(gadget)
    delegate.add_client(client)
    yield delegate


@pytest.fixture()
def network():
    network = DummyNetworkConnector(HOSTNAME)
    yield network


@pytest.fixture()
def network_manager(network):
    manager = NetworkManager()
    manager.add_connector(network)
    yield manager
    manager.__del__()


@pytest.fixture()
def api(delegate: DummyApiDelegate, network_manager: NetworkManager):
    api = ApiManager(delegate, network_manager)
    yield api
    api.__del__()


@pytest.mark.bridge
def test_api_unknown(api: ApiManager, network: DummyNetworkConnector):
    network.mock_receive("unknown_path",
                         REQ_SENDER,
                         {"test": 0x01})


@pytest.mark.bridge
def test_api_heartbeat(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    network.mock_receive("heartbeat",
                         REQ_SENDER,
                         {"test": 0x01})
    assert delegate.get_last_heartbeat_name() is None
    assert delegate.get_last_heartbeat_runtime() is None

    network.mock_receive("heartbeat",
                         REQ_SENDER,
                         {"runtime_id": REQ_RUNTIME})
    assert delegate.get_last_heartbeat_name() == REQ_SENDER
    assert delegate.get_last_heartbeat_runtime() == REQ_RUNTIME


@pytest.mark.bridge
def test_api_gadget_sync(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    network.mock_receive("sync/gadget",
                         REQ_SENDER,
                         {"gadget": {"yolo": "blub"}})
    assert delegate.get_last_gadget() is None

    network.mock_receive("sync/gadget",
                         REQ_SENDER,
                         {
                             "gadget": GADGET_CONFIG_ERR
                         })
    assert delegate.get_last_gadget() is None

    network.mock_receive("sync/gadget",
                         REQ_SENDER,
                         GADGET_CONFIG_OK)
    assert delegate.get_last_gadget() is not None
    assert delegate.get_last_gadget().get_name() == GADGET_NAME


@pytest.mark.bridge
def test_api_handle_gadget_update(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    delegate.add_gadget(Gadget(
        GADGET_NAME,
        "spongolopolus",
        [Characteristic(
            CharacteristicIdentifier.status,
            0,
            1,
            1,
            1
        )]))

    network.mock_receive("update/gadget",
                         REQ_SENDER,
                         {"gadget": {"yolo": "blub"}})
    assert delegate.get_last_gadget() is None

    network.mock_receive("update/gadget",
                         REQ_SENDER,
                         GADGET_UPDATE_ERR)
    assert delegate.get_last_gadget() is None

    network.mock_receive("update/gadget",
                         REQ_SENDER,
                         GADGET_UPDATE_ERR_UNKNOWN)
    assert delegate.get_last_gadget() is None

    network.mock_receive("update/gadget",
                         REQ_SENDER,
                         GADGET_UPDATE_OK)
    assert delegate.get_last_gadget() is not None
    assert delegate.get_last_gadget().get_characteristic_types()[0] == GADGET_CHARACTERISTIC_TYPE


@pytest.mark.bridge
def test_api_client_sync(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    network.mock_receive("sync/client",
                         REQ_SENDER,
                         {"client":
                             {
                                 "yolo": "blub"
                             }
                         })
    assert delegate.get_last_client() is None

    network.mock_receive("sync/client",
                         REQ_SENDER,
                         payload=CLIENT_CONFIG_OK)
    assert delegate.get_last_client() is not None
    assert delegate.get_last_client().get_runtime_id() == REQ_RUNTIME
    assert delegate.get_last_client().get_name() == REQ_SENDER
    assert delegate.get_last_gadget() is not None
    assert delegate.get_last_gadget().get_name() == GADGET_NAME


@pytest.mark.bridge
def test_api_client_reboot(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    delegate.add_client(SmarthomeClient("spongo",
                                        123123123,
                                        datetime.datetime.utcnow(),
                                        "213132",
                                        "fb_420",
                                        {},
                                        1))

    network.mock_receive("reboot/client",
                         REQ_SENDER,
                         {"client": "spongo"})

    network.mock_receive("reboot/client",
                         REQ_SENDER,
                         {"id": "spongo"})

@pytest.mark.bridge
def test_api_request_sync(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    api.request_sync(REQ_SENDER)
    last_send = network.get_last_send_req()
    assert last_send is not None
    assert last_send.get_receiver() == REQ_SENDER
    assert last_send.get_sender() == HOSTNAME


@pytest.mark.bridge
def test_api_send_gadget_update(api: ApiManager, network: DummyNetworkConnector, f_any_gadget, f_dummy_gadget):
    api.send_gadget_update(f_any_gadget)
    assert network.get_last_send_req() is not None
    assert network.get_last_send_req().get_receiver() is None

    network.reset()

    api.send_gadget_update(f_dummy_gadget)
    assert network.get_last_send_req() is None


@pytest.mark.bridge
def test_api_get_bridge_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive("info/bridge",
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_info_response")


@pytest.mark.bridge
def test_api_get_gadget_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive("info/gadgets",
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_all_gadgets_response")


@pytest.mark.bridge
def test_api_get_client_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive("info/clients",
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_all_clients_response")
