import pytest
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from smarthome_bridge.gadgets.gadget import GadgetIdentifier
from smarthome_bridge.gadgets.any_gadget import AnyGadget

C_TYPE = CharacteristicIdentifier.fanSpeed
C_MIN = 0
C_MAX = 100
C_STEPS = 4


@pytest.fixture()
def f_characteristic_fan_speed():
    characteristic = Characteristic(c_type=C_TYPE,
                                    min_val=C_MIN,
                                    max_val=C_MAX,
                                    steps=C_STEPS)
    yield characteristic
    # characteristic.__del__()


ANY_NAME = "any_gadget"
ANY_TYPE = GadgetIdentifier.any_gadget
ANY_HOST = "test_host"


@pytest.fixture()
def f_any_gadget(f_characteristic_fan_speed):
    gadget = AnyGadget(name=ANY_NAME,
                       host_client=ANY_HOST,
                       characteristics=[f_characteristic_fan_speed])
    yield gadget
    gadget.__del__()
