import pytest

from network.mqtt_credentials_container import MqttCredentialsContainer
from gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from gadget_publishers.gadget_publisher_homebridge import GadgetPublisherHomeBridge,\
    GadgetCreationError, GadgetDeletionError
from gadgets.fan_westinghouse_ir import FanWestinghouseIR
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from gadgets.remote_gadget import RemoteGadget


HOMEBRIDGE_NETWORK_NAME = "test_network"
GADGET_NAME = "unittest_gadget"


@pytest.fixture()
def gadget():
    gadget = FanWestinghouseIR(GADGET_NAME,
                               HOMEBRIDGE_NETWORK_NAME,
                               Characteristic(CharacteristicIdentifier.status,
                                              0,
                                              1,
                                              1),
                               Characteristic(CharacteristicIdentifier.fan_speed,
                                              0,
                                              100,
                                              4))
    yield gadget
    gadget.__del__()


@pytest.fixture()
def homebridge_network(f_mqtt_credentials: MqttCredentialsContainer):
    network_connector = HomebridgeNetworkConnector(HOMEBRIDGE_NETWORK_NAME,
                                                   f_mqtt_credentials,
                                                   1)
    yield network_connector
    network_connector.__del__()


@pytest.fixture()
def publisher_network(homebridge_network: HomebridgeNetworkConnector, gadget: FanWestinghouseIR):
    connector = GadgetPublisherHomeBridge(homebridge_network)

    try:
        connector.remove_gadget(gadget.get_name())
    except GadgetDeletionError:
        pass

    yield connector

    try:
        connector.remove_gadget(gadget.get_name())
    except GadgetDeletionError:
        pass


@pytest.mark.network
@pytest.mark.bridge
def test_gadget_publisher_homebridge_network(publisher_network: GadgetPublisherHomeBridge, gadget: RemoteGadget):
    with pytest.raises(GadgetDeletionError):
        publisher_network.remove_gadget(gadget.get_name())

    publisher_network.create_gadget(gadget)

    with pytest.raises(GadgetCreationError):
        publisher_network.create_gadget(gadget)

    publisher_network.remove_gadget(gadget.get_name())

    fan_speed = gadget.get_characteristic(CharacteristicIdentifier.fan_speed)
    fan_speed.set_step_value(2)

    publisher_network.receive_gadget(gadget)

    fan_speed.set_step_value(3)

    publisher_network.receive_gadget(gadget)

    publisher_network.remove_gadget(gadget.get_name())


@pytest.mark.bridge
def test_gadget_publisher_homebridge_mock():
    pass
