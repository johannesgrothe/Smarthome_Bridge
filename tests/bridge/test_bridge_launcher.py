import pytest
import time

from smarthome_bridge.bridge_launcher import BridgeLauncher

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

    print("Sleeping for 30 seconds")
    time.sleep(30)
    print("Noice")

    bridge.__del__()
