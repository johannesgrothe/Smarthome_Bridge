import pytest

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer

NAME = "unittest"
HOST = "unittest_host"


class DummyGadgetUpdateContainer(GadgetUpdateContainer):
    _dummy_attribute: bool

    def __int__(self, origin: str):
        super().__init__(origin)
        self._dummy_attribute = False

    @property
    def dummy_attribute(self) -> bool:
        with self._get_lock():
            return self._dummy_attribute

    def set_dummy_attribute(self):
        with self._get_lock():
            self._dummy_attribute = True
            self._record_change()


class DummyGadget(Gadget):
    _update_container = DummyGadgetUpdateContainer

    def reset_updated_properties(self):
        self._update_container = DummyGadgetUpdateContainer(self.id)

    def set_int_attribute(self, value: int):
        if value < 0:
            raise ValueError("oi, dont go into the negative mate")
        self._update_container.set_dummy_attribute()


@pytest.fixture()
def gadget() -> DummyGadget:
    gadget = DummyGadget(NAME)
    yield gadget
    gadget.__del__()


@pytest.mark.bridge
def test_gadget_getters(gadget):
    assert gadget.name == NAME
