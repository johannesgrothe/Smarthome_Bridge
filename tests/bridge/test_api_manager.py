import pytest

from smarthome_bridge.api_manager import ApiManager
from smarthome_bridge.network_manager import NetworkManager
from test_helpers.dummy_api_delegate import DummyApiDelegate
from network.request import Request

REQ_SENDER = "unittest"
REQ_RUNTIME = 123456

GADGET_NAME = "test_fan"


@pytest.fixture()
def delegate():
    delegate = DummyApiDelegate()
    yield delegate


@pytest.fixture()
def network_manager():
    manager = NetworkManager()
    yield manager
    manager.__del__()


@pytest.fixture()
def api(delegate: DummyApiDelegate, network_manager: NetworkManager):
    api = ApiManager(delegate, network_manager)
    yield api
    api.__del__()


@pytest.mark.bridge
def test_api_unknown(api: ApiManager, network_manager: NetworkManager, delegate: DummyApiDelegate):
    heartbeat_req = Request("yolokopter",
                            None,
                            REQ_SENDER,
                            None,
                            {"test": 0x01})
    network_manager.receive(heartbeat_req)


@pytest.mark.bridge
def test_api_heartbeat(api: ApiManager, network_manager: NetworkManager, delegate: DummyApiDelegate):
    heartbeat_req = Request("heartbeat",
                            None,
                            REQ_SENDER,
                            None,
                            {"test": 0x01})
    network_manager.receive(heartbeat_req)
    assert delegate.get_last_heartbeat_name() is None
    assert delegate.get_last_heartbeat_runtime() is None

    heartbeat_req = Request("heartbeat",
                            None,
                            REQ_SENDER,
                            None,
                            {"runtime_id": REQ_RUNTIME})
    network_manager.receive(heartbeat_req)
    assert delegate.get_last_heartbeat_name() == REQ_SENDER
    assert delegate.get_last_heartbeat_runtime() == REQ_RUNTIME


@pytest.mark.bridge
def test_api_gadget_sync(api: ApiManager, network_manager: NetworkManager, delegate: DummyApiDelegate):
    sync_req = Request("sync/gadget",
                       None,
                       REQ_SENDER,
                       None,
                       {"gadget":
                           {
                               "yolo": "blub"
                           }
                       })
    network_manager.receive(sync_req)
    assert delegate.get_last_gadget() is None

    sync_req = Request("sync/gadget",
                       None,
                       REQ_SENDER,
                       None,
                       payload={
                           "gadget": {
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
                       })
    network_manager.receive(sync_req)
    assert delegate.get_last_gadget() is None

    sync_req = Request("sync/gadget",
                       None,
                       REQ_SENDER,
                       None,
                       payload={
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
                       })
    network_manager.receive(sync_req)
    assert delegate.get_last_gadget() is not None
    assert delegate.get_last_gadget().get_name() == GADGET_NAME
