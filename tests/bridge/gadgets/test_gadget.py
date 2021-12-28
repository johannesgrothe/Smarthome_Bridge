import pytest

from gadgets.any_gadget import AnyGadget
from system.gadget_definitions import GadgetIdentifier
from gadgets.gadget_event_mapping import GadgetEventMapping
from smarthome_bridge.characteristic import CharacteristicIdentifier

NAME = "unittest"
HOST = "unittest_host"


@pytest.mark.bridge
def test_gadget_getters(f_characteristic_status):
    gadget = AnyGadget(NAME,
                       HOST,
                       [f_characteristic_status])
    assert gadget.get_name() == NAME
    assert gadget.get_host_client() == HOST
    assert len(gadget.get_characteristic_types()) == 1
    assert gadget.get_characteristics() == [f_characteristic_status]
    assert gadget.get_characteristic(CharacteristicIdentifier.status) == f_characteristic_status
    assert gadget.get_characteristic(CharacteristicIdentifier.fan_speed) is None


@pytest.mark.bridge
def test_gadget_event_mapping(f_characteristic_status):
    gadget = AnyGadget(NAME,
                       HOST,
                       [f_characteristic_status])
    mapping = [GadgetEventMapping("b0ng0", [(1, 1)])]
    gadget.set_event_mapping(mapping)
    assert gadget.get_event_mapping() == mapping
