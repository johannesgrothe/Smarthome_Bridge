import datetime

import pytest

from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.network_manager import NetworkManager
from test_helpers.dummy_network_connector import DummyNetworkConnector
from smarthome_bridge.client import Client, ClientSoftwareInformationContainer
from gadgets.remote.i_remote_gadget import IRemoteGadget
from system.api_definitions import ApiURIs
from system.utils.software_version import SoftwareVersion
from utils.client_config_manager import ClientConfigManager, ConfigDoesNotExistException

HOSTNAME = "unittest_host"
REQ_SENDER = "unittest"
REQ_RUNTIME = 123456

GADGET_NAME = "test_fan"
CLIENT_NAME = "test_client"

T_TIMESTAMP = datetime.datetime.now()

GADGET_CONFIG_OK = {
    "gadget": {
        "type": 3,
        "id": GADGET_NAME,
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
#
# GADGET_UPDATE_ERR = {
#     "id": GADGET_NAME,
#     "characteristics": [{
#         "type": GADGET_CHARACTERISTIC_TYPE,
#     }]
# }
#
# GADGET_UPDATE_ERR_UNKNOWN = {
#     "id": "blubb",
#     "characteristics": [{
#         "type": GADGET_CHARACTERISTIC_TYPE,
#         "step_value": 0
#     }]
# }
#
# GADGET_UPDATE_OK = {
#     "id": GADGET_NAME,
#     "characteristics": [{
#         "type": GADGET_CHARACTERISTIC_TYPE,
#         "step_value": 0
#     }]
# }

CLIENT_CONFIG_OK = {
    "client": {
        "runtime_id": REQ_RUNTIME,
        "port_mapping": {},
        "boot_mode": 1,
        "sw_uploaded": None,
        "sw_commit": None,
        "sw_branch": None,
        "api_version": "1.3.7",
    },
    "gadgets": [
        GADGET_CONFIG_OK["gadget"]
    ]
}

CONFIG_SAVE = {
    "$schema": "./../system/json_schemas/client_config.json",
    "name": "Spongo",
    "description": "Example config for testing",
    "system": {
        "id": "YoloChip14",
        "wifi_ssid": "test_wifi",
        "wifi_pw": "test_pw",
        "mqtt_ip": "192.168.178.111",
        "mqtt_port": 1883,
        "mqtt_user": "null",
        "mqtt_pw": "pw",
        "irrecv_pin": 4,
        "irsend_pin": 5,
        "radio_recv_pin": 6,
        "radio_send_pin": 7,
        "network_mode": 2,
        "gadget_remote": 1,
        "code_remote": 1,
        "event_remote": 1
    },
    "gadgets": {
        "gadgets": []
    },
    "events": {
        "events": []
    }
}


# @pytest.fixture()
# def gadget():
#     gadget = FanWestinghouseIR(GADGET_NAME,
#                                CLIENT_NAME,
#                                Characteristic(CharacteristicIdentifier.status,
#                                               0,
#                                               1),
#                                Characteristic(CharacteristicIdentifier.fan_speed,
#                                               0,
#                                               100,
#                                               4))
#     yield gadget
#     gadget.__del__()


@pytest.fixture()
def client():
    client = Client(CLIENT_NAME,
                    1773,
                    ClientSoftwareInformationContainer("t_commit",
                                                       "t_branch",
                                                       T_TIMESTAMP),
                    {},
                    1,
                    SoftwareVersion(1, 3, 6))
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
    manager.set_default_timeout(2)
    yield manager
    manager.__del__()


@pytest.fixture()
def api(delegate: DummyApiDelegate, network_manager: NetworkManager):
    api = ApiManager(delegate, network_manager)
    yield api
    api.__del__()


@pytest.fixture()
def config_manager():
    manager = ClientConfigManager()
    yield manager


@pytest.fixture()
def debug_config_doesnt_exist(config_manager: ClientConfigManager):
    try:
        config_manager.delete_config_file(CONFIG_SAVE["name"])
    except ConfigDoesNotExistException:
        pass
    yield CONFIG_SAVE
    try:
        config_manager.delete_config_file(CONFIG_SAVE["name"])
    except ConfigDoesNotExistException:
        pass


@pytest.fixture()
def debug_config(config_manager: ClientConfigManager, debug_config_doesnt_exist: dict):
    config_manager.write_config(CONFIG_SAVE, overwrite=True)
    yield CONFIG_SAVE


@pytest.mark.bridge
def test_api_unknown(api: ApiManager, network: DummyNetworkConnector):
    network.mock_receive("unknown_path",
                         REQ_SENDER,
                         {"test": 0x01})


@pytest.mark.bridge
def test_api_heartbeat(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    network.mock_receive(ApiURIs.heartbeat.uri,
                         REQ_SENDER,
                         {"test": 0x01})
    assert delegate.get_last_heartbeat_name() is None
    assert delegate.get_last_heartbeat_runtime() is None

    network.mock_receive(ApiURIs.heartbeat.uri,
                         REQ_SENDER,
                         {"runtime_id": REQ_RUNTIME})
    assert delegate.get_last_heartbeat_name() == REQ_SENDER
    assert delegate.get_last_heartbeat_runtime() == REQ_RUNTIME


@pytest.mark.bridge
def test_api_handle_gadget_update(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    delegate.add_gadget(IRemoteGadget(
        GADGET_NAME,
        "spongolopolus",
        [Characteristic(
            CharacteristicIdentifier.status,
            0,
            1,
            1,
            1
        )]))

    network.mock_receive(ApiURIs.update_gadget.uri,
                         REQ_SENDER,
                         {"gadget": {"yolo": "blub"}})
    assert delegate.get_last_gadget_update() is None

    network.mock_receive(ApiURIs.update_gadget.uri,
                         REQ_SENDER,
                         GADGET_UPDATE_ERR)
    assert delegate.get_last_gadget_update() is None

    network.mock_receive(ApiURIs.update_gadget.uri,
                         REQ_SENDER,
                         GADGET_UPDATE_ERR_UNKNOWN)
    assert delegate.get_last_gadget_update() is None

    network.mock_receive(ApiURIs.update_gadget.uri,
                         REQ_SENDER,
                         GADGET_UPDATE_OK)
    assert delegate.get_last_gadget_update() is not None
    assert delegate.get_last_gadget_update().get_characteristic_types()[0] == GADGET_CHARACTERISTIC_TYPE


@pytest.mark.bridge
def test_api_client_sync(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    network.mock_receive(ApiURIs.sync_client.uri,
                         REQ_SENDER,
                         {"client":
                             {
                                 "yolo": "blub"
                             }
                         })
    assert delegate.get_last_client() is None

    network.mock_receive(ApiURIs.sync_client.uri,
                         REQ_SENDER,
                         payload=CLIENT_CONFIG_OK)
    assert delegate.get_last_client() is not None
    assert delegate.get_last_client().get_runtime_id() == REQ_RUNTIME
    assert delegate.get_last_client().get_name() == REQ_SENDER
    assert delegate.get_last_gadget() is not None
    assert delegate.get_last_gadget().get_name() == GADGET_NAME


@pytest.mark.bridge
def test_api_client_reboot(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate):
    # TODO: finish test!
    delegate.add_client(Client("spongo",
                               123123123,
                               datetime.datetime.utcnow(),
                               "213132",
                               "fb_420",
                               {},
                               1,
                               SoftwareVersion(3, 4, 12)))

    network.mock_receive(ApiURIs.client_reboot.uri,
                         REQ_SENDER,
                         {"client": "spongo"})

    network.mock_receive(ApiURIs.client_reboot.uri,
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
def test_api_send_gadget_update(api: ApiManager, network: DummyNetworkConnector, f_any_gadget):
    api.send_gadget_update(f_any_gadget)
    assert network.get_last_send_req() is not None
    assert network.get_last_send_req().get_receiver() is None


@pytest.mark.bridge
def test_api_get_bridge_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive(ApiURIs.info_bridge.uri,
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_info_response")


@pytest.mark.bridge
def test_api_get_gadget_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive(ApiURIs.info_gadgets.uri,
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_all_gadgets_response")


@pytest.mark.bridge
def test_api_get_client_info(api: ApiManager, network: DummyNetworkConnector, delegate: DummyApiDelegate, f_validator):
    assert network.get_last_send_response() is None
    network.mock_receive(ApiURIs.info_clients.uri,
                         REQ_SENDER,
                         {})
    resp = network.get_last_send_response()
    assert resp is not None
    assert resp.get_receiver() == REQ_SENDER
    f_validator.validate(resp.get_payload(), "api_get_all_clients_response")


@pytest.mark.bridge
def test_api_get_all_configs(api: ApiManager, network: DummyNetworkConnector, debug_config: dict, f_validator):
    network.mock_receive(ApiURIs.config_storage_get_all.uri, REQ_SENDER, {})
    response = network.get_last_send_response()
    assert response is not None
    assert debug_config["name"] in response.get_payload()["configs"]
    assert response.get_payload()["configs"][debug_config["name"]] == debug_config["description"]
    f_validator.validate(response.get_payload(), "api_config_get_all_response")


@pytest.mark.bridge
def test_api_get_config(api: ApiManager, network: DummyNetworkConnector, debug_config: dict, f_validator):
    conf_name = {"name": debug_config["name"]}
    network.mock_receive(ApiURIs.config_storage_get.uri,
                         REQ_SENDER,
                         conf_name)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_payload()["config"]["name"] == conf_name["name"]
    f_validator.validate(response.get_payload(), "api_config_get_response")

    conf_name_illegal = {"name": "Unicorn"}
    network.mock_receive(ApiURIs.config_storage_get.uri,
                         REQ_SENDER,
                         conf_name_illegal)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_payload()["error_type"] == "ConfigDoesNotExistException"


@pytest.mark.bridge
def test_api_save_config(api: ApiManager, network: DummyNetworkConnector, debug_config_doesnt_exist: dict):
    conf_payload_overwrite = {
        "config": debug_config_doesnt_exist,
        "overwrite": True
    }
    conf_payload = {
        "config": debug_config_doesnt_exist,
        "overwrite": False
    }

    # save without overwrite (initial)
    network.mock_receive(ApiURIs.config_storage_save.uri,
                         REQ_SENDER,
                         conf_payload)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_ack() is True

    # save with overwrite
    network.mock_receive(ApiURIs.config_storage_save.uri,
                         REQ_SENDER,
                         conf_payload_overwrite)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_ack() is True

    # save without overwrite
    network.mock_receive(ApiURIs.config_storage_save.uri,
                         REQ_SENDER,
                         conf_payload)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_payload()["error_type"] == "ConfigAlreadyExistsException"


@pytest.mark.bridge
def test_api_delete_config(api: ApiManager, network: DummyNetworkConnector, debug_config: dict):
    conf_payload = {
        "name": debug_config["name"]
    }
    network.mock_receive(ApiURIs.config_storage_delete.uri,
                         REQ_SENDER,
                         conf_payload)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_ack() is True

    network.mock_receive(ApiURIs.config_storage_delete.uri,
                         REQ_SENDER,
                         conf_payload)
    response = network.get_last_send_response()
    assert response is not None
    assert response.get_payload()["error_type"] == "ConfigDoesNotExistException"
