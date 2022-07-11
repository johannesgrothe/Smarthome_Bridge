import pytest

from gadgets.gadget_update_container import GadgetUpdateContainer


@pytest.fixture()
def gadget_update_container():
    container = GadgetUpdateContainer("yolokopter")
    yield container


@pytest.mark.bridge
def test_gadget_update_container(gadget_update_container: GadgetUpdateContainer):
    assert gadget_update_container.is_empty
    gadget_update_container.set_name()
    assert not gadget_update_container.is_empty
