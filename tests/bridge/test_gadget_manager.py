import pytest
import random

from smarthome_bridge.gadget_manager import GadgetManager

from test_helpers.gadget_fixtures import f_any_gadget, ANY_NAME, ANY_TYPE, ANY_HOST

from test_helpers.gadget_fixtures import *


@pytest.fixture()
def gadget_manager():
    manager = GadgetManager()
    yield manager
    manager.__del__()


@pytest.mark.bridge
def test_gadget_manager(gadget_manager, f_any_gadget):
    assert True
