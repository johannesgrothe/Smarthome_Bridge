import pytest

from smarthome_bridge.gadgets.gadget_factory import GadgetFactory, GadgetCreationError
from smarthome_bridge.gadgets.gadget import GadgetIdentifier

from smarthome_bridge.gadgets.any_gadget import AnyGadget
from smarthome_bridge.gadgets.lamp_neopixel_basic import LampNeopixelBasic


GADGET_NAME = "unittest"
GADGET_HOST = "unittest_host"


@pytest.fixture()
def factory():
    factory = GadgetFactory()
    yield factory


@pytest.mark.bridge
def test_gadget_factory_any_gadget(factory: GadgetFactory, f_characteristic_fan_speed, f_any_gadget: AnyGadget):
    with pytest.raises(NotImplementedError):
        factory.create_gadget(gadget_type=f_any_gadget.get_type(),
                              name=f_any_gadget.get_name(),
                              host_client=f_any_gadget.get_host_client(),
                              characteristics=[f_characteristic_fan_speed])
    factory_gadget = factory.create_any_gadget(name=f_any_gadget.get_name(),
                                               host_client=f_any_gadget.get_host_client(),
                                               characteristics=f_any_gadget.get_characteristics())
    assert type(factory_gadget) == type(f_any_gadget)
    assert factory_gadget == f_any_gadget


@pytest.mark.bridge
def test_gadget_factory_lamp_neopixel_basic(factory: GadgetFactory, f_characteristic_status,
                                            f_characteristic_brightness, f_characteristic_hue):
    with pytest.raises(GadgetCreationError):
        factory.create_gadget(GadgetIdentifier.lamp_neopixel_basic,
                              GADGET_NAME,
                              GADGET_HOST,
                              [])
    factory_gadget = factory.create_gadget(GadgetIdentifier.lamp_neopixel_basic,
                                           GADGET_NAME,
                                           GADGET_HOST,
                                           [f_characteristic_status,
                                            f_characteristic_hue,
                                            f_characteristic_brightness])

    assert factory_gadget == LampNeopixelBasic(GADGET_NAME,
                                               GADGET_HOST,
                                               f_characteristic_status,
                                               f_characteristic_brightness,
                                               f_characteristic_hue)
