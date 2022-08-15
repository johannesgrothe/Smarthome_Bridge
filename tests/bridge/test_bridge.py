import pytest

from smarthome_bridge.bridge import Bridge


BRIDGE_NAME = "test_bridge"


@pytest.fixture()
def bridge(f_temp_exists):
    bridge = Bridge(BRIDGE_NAME, f_temp_exists)
    yield bridge
    bridge.__del__()


@pytest.mark.bridge
def test_bridge(bridge: Bridge):
    assert bridge.info.name == BRIDGE_NAME
