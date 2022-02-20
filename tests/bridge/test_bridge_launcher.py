import pytest

from smarthome_bridge.bridge_launcher import BridgeLauncher
from test_helpers.timing_organizer import TimingOrganizer

BRIDGE_NAME = "test_bridge"
BRIDGE_API_PORT = 6000
BRIDGE_SOCKET_PORT = 6001
BRIDGE_DEFAULT_USER_NAME = "testuser"
BRIDGE_DEFAULT_USER_PW = "testpw"


@pytest.fixture()
def launcher():
    launch = BridgeLauncher()
    yield launch


@pytest.mark.bridge
def test_bridge_launcher(launcher: BridgeLauncher):
    print("Launching Bridge")
    bridge = launcher.launch(BRIDGE_NAME,
                             None,
                             BRIDGE_API_PORT,
                             BRIDGE_SOCKET_PORT,
                             True,
                             (BRIDGE_DEFAULT_USER_NAME, BRIDGE_DEFAULT_USER_PW),
                             True)

    TimingOrganizer.delay(30000)

    bridge.__del__()
