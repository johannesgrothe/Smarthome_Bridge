import pytest

from smarthome_bridge.gadgets.gadget import Gadget
from test_helpers.gadget_fixtures import *


@pytest.mark.bridge
def test_gadget_getters(f_any_gadget: Gadget):
    assert f_any_gadget.get_name() == ANY_NAME
    assert f_any_gadget.get_type() == ANY_TYPE
    assert f_any_gadget.get_host_client() == ANY_HOST
    assert len(f_any_gadget.get_characteristic_types()) == 1
