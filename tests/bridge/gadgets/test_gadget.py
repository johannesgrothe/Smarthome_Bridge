import pytest

from gadgets.gadget import Gadget

NAME = "unittest"
HOST = "unittest_host"


class DummyGadget(Gadget):

    def reset_updated_properties(self):
        pass


@pytest.fixture()
def gadget() -> DummyGadget:
    gadget = DummyGadget(NAME)
    yield gadget
    gadget.__del__()


@pytest.mark.bridge
def test_gadget_getters(gadget):
    assert gadget.name == NAME
