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
    bridge = launcher.launch(name=BRIDGE_NAME,
                             mqtt=None,
                             api_port=BRIDGE_API_PORT,
                             socket_port=BRIDGE_SOCKET_PORT,
                             serial_active=True,
                             static_user_data=(BRIDGE_DEFAULT_USER_NAME, BRIDGE_DEFAULT_USER_PW),
                             homekit_active=False,
                             add_dummy_data=True)

    TimingOrganizer.delay(30000)

    bridge.__del__()
