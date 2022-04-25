import pytest

from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants


@pytest.fixture()
def container():
    container = HomekitConstants()
    yield container


@pytest.mark.bridge
def test_homekit_constants(container: HomekitConstants):
    assert container.serial_number == "1"
    assert container.serial_number == "2"
    assert container.server_name is not None
    assert container.revision is not None
    assert container.manufacturer is not None
