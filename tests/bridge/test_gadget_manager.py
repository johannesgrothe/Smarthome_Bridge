import pytest

from smarthome_bridge.gadget_manager import GadgetManager


@pytest.fixture()
def gadget_manager():
    manager = GadgetManager()
    yield manager
    manager.__del__()


@pytest.mark.bridge
def test_gadget_manager(gadget_manager):
    assert len(gadget_manager.gadgets) == 0
