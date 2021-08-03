import pytest

from smarthome_bridge.gadgets.gadget_factory import GadgetFactory
from smarthome_bridge.gadgets.any_gadget import AnyGadget
from test_helpers.gadget_fixtures import f_characteristic_fan_speed
from test_helpers.gadget_fixtures import f_any_gadget, ANY_NAME, ANY_TYPE, ANY_HOST


@pytest.fixture()
def factory():
    factory = GadgetFactory()
    yield factory
    # factory.__del__()


@pytest.mark.bridge
def test_gadget_factory_any_gadget(factory: GadgetFactory, f_characteristic_fan_speed, f_any_gadget: AnyGadget):
    factory_gadget = factory.create_gadget(gadget_type=ANY_TYPE,
                                           name=ANY_NAME,
                                           host_client=ANY_HOST,
                                           characteristics=[f_characteristic_fan_speed])
    assert type(factory_gadget) == type(f_any_gadget)
    assert factory_gadget == f_any_gadget
