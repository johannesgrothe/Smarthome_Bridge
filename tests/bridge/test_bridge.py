import pytest

from smarthome_bridge.bridge import Bridge


BRIDGE_NAME = "test_bridge"


@pytest.fixture()
def bridge():
    bridge = Bridge(BRIDGE_NAME)
    yield bridge
    bridge.__del__()


@pytest.mark.bridge
def test_bridge(bridge: Bridge):
    assert bridge.get_name() == BRIDGE_NAME
