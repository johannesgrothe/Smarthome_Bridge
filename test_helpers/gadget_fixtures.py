import pytest
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from gadgets.any_gadget import AnyGadget


@pytest.fixture()
def f_characteristic_status():
    characteristic = Characteristic(c_type=CharacteristicIdentifier.status,
                                    min_val=0,
                                    max_val=1)
    yield characteristic


@pytest.fixture()
def f_characteristic_fan_speed():
    characteristic = Characteristic(c_type=CharacteristicIdentifier.fan_speed,
                                    min_val=0,
                                    max_val=100,
                                    steps=4)
    yield characteristic


@pytest.fixture()
def f_characteristic_brightness():
    characteristic = Characteristic(c_type=CharacteristicIdentifier.brightness,
                                    min_val=0,
                                    max_val=100)
    yield characteristic


@pytest.fixture()
def f_characteristic_hue():
    characteristic = Characteristic(c_type=CharacteristicIdentifier.hue,
                                    min_val=0,
                                    max_val=0xFF)
    yield characteristic


@pytest.fixture()
def f_characteristic_saturation():
    characteristic = Characteristic(c_type=CharacteristicIdentifier.saturation,
                                    min_val=0,
                                    max_val=100)
    yield characteristic


@pytest.fixture()
def f_any_gadget(f_characteristic_fan_speed):
    gadget = AnyGadget(name="any_gadget",
                       host_client="any_host",
                       characteristics=[f_characteristic_fan_speed])
    yield gadget
    gadget.__del__()
