import os

import pytest

from gadget_publishers.gadget_publisher import GadgetDeletionError, GadgetCreationError
from gadget_publishers.homekit.homekit_config_manager import HomekitConfigManager
from gadgets.gadget import Gadget
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from smarthome_bridge.characteristic import Characteristic
from system.gadget_definitions import CharacteristicIdentifier
from test_helpers.dummy_status_supplier import DummyStatusSupplier
from test_helpers.timing_organizer import TimingOrganizer

CONFIG_NAME = "hb_test_cfg.json"
GADGET_NAME = "unittest_gadget"


@pytest.fixture()
def status_supplier():
    supplier = DummyStatusSupplier()
    return supplier


@pytest.fixture()
def config(f_temp_exists: str):
    cfg_path = os.path.join(f_temp_exists, CONFIG_NAME)
    manager = HomekitConfigManager(cfg_path)
    manager.generate_new_config()
    return manager.path


@pytest.fixture()
def gadget():
    gadget = LampNeopixelBasic(GADGET_NAME,
                               "test",
                               Characteristic(CharacteristicIdentifier.status,
                                              0,
                                              1,
                                              1),
                               Characteristic(CharacteristicIdentifier.hue,
                                              0,
                                              360,
                                              360),
                               Characteristic(CharacteristicIdentifier.brightness,
                                              0,
                                              100,
                                              100),
                               Characteristic(CharacteristicIdentifier.saturation,
                                              0,
                                              100,
                                              100))
    yield gadget
    gadget.__del__()


@pytest.fixture()
def publisher(config: str):
    connector = GadgetPublisherHomekit(config)
    yield connector
    connector.__del__()


@pytest.mark.github_skip  # TODO: fix github issue: AttributeError: 'Zeroconf' object has no attribute 'check_service'
@pytest.mark.bridge
def test_gadget_publisher_homekit(publisher: GadgetPublisherHomekit, gadget: Gadget, status_supplier: DummyStatusSupplier):
    with pytest.raises(GadgetDeletionError):
        publisher.remove_gadget(gadget.get_name())

    publisher.receive_gadget(gadget)

    with pytest.raises(GadgetCreationError):
        publisher.create_gadget(gadget)

    gadget.get_characteristic(CharacteristicIdentifier.hue).set_step_value(55)
    publisher.set_status_supplier(status_supplier)
    gadget.get_characteristic(CharacteristicIdentifier.hue).set_step_value(65)
    status_supplier.gadgets.append(gadget)
    gadget.get_characteristic(CharacteristicIdentifier.hue).set_step_value(75)

    publisher.receive_gadget(gadget)

    timer = TimingOrganizer()

    print("Awaiting server restart")
    timer.delay(10000)

    publisher.remove_gadget(gadget.get_name())

    timer.delay(2000)

    publisher.__del__()
