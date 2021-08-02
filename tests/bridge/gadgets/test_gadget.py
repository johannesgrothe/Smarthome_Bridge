import pytest

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier


G_NAME = "test_gadget"
G_TYPE = GadgetIdentifier.fan_westinghouse_ir
G_CLIENT = "test_client"
G_RUNTIME_ID = 12345

C_TYPE = CharacteristicIdentifier.fanSpeed
C_MIN = 0
C_MAX = 100
C_STEPS = 4
G_CHARACTERISTICS = [Characteristic(c_type=C_TYPE,
                                    min_val=C_MIN,
                                    max_val=C_MAX,
                                    steps=C_STEPS)]


@pytest.fixture()
def gadget():
    gadget = Gadget(name=G_NAME,
                    g_type=G_TYPE,
                    host_client=G_CLIENT,
                    host_client_runtime_id=G_RUNTIME_ID,
                    characteristics=G_CHARACTERISTICS)
    yield gadget
    gadget.__del__()


@pytest.mark.bridge
def test_gadget_getters(gadget: Gadget):
    assert gadget.get_name() == G_NAME
    assert gadget.get_type() == G_TYPE
    assert gadget.get_host_client() == G_CLIENT
