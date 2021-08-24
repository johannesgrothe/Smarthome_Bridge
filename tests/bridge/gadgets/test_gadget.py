import pytest

from smarthome_bridge.gadgets.any_gadget import AnyGadget
from smarthome_bridge.gadgets.gadget import GadgetIdentifier
from smarthome_bridge.characteristic import CharacteristicIdentifier


NAME = "unittest"
HOST = "unittest_host"


@pytest.mark.bridge
def test_gadget_getters(f_characteristic_status):
    gadget = AnyGadget(NAME,
                       HOST,
                       [f_characteristic_status])
    assert gadget.get_name() == NAME
    assert gadget.get_type() == GadgetIdentifier.any_gadget
    assert gadget.get_host_client() == HOST
    assert len(gadget.get_characteristic_types()) == 1
    assert gadget.get_characteristics() == [f_characteristic_status]
    assert gadget.get_characteristic(CharacteristicIdentifier.status) == f_characteristic_status
    assert gadget.get_characteristic(CharacteristicIdentifier.fanSpeed) is None
