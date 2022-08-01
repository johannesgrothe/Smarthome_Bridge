import os

import pytest

from gadget_publishers.gadget_publisher import GadgetDeletionError, GadgetCreationError
from gadget_publishers.homekit.homekit_config_manager import HomekitConfigManager
from gadgets.gadget import Gadget
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from smarthome_bridge.client_information_interface import ClientInformationInterface
from test_helpers.timing_organizer import TimingOrganizer

CONFIG_NAME = "hb_test_cfg.json"
GADGET_NAME = "unittest_gadget"


class DummyClient(ClientInformationInterface):

    def _is_active(self) -> bool:
        return True

    def _get_id(self) -> str:
        return "dummy_client"


@pytest.fixture()
def config(f_temp_exists: str):
    cfg_path = os.path.join(f_temp_exists, CONFIG_NAME)
    manager = HomekitConfigManager(cfg_path)
    manager.generate_new_config()
    return manager.path


@pytest.fixture()
def client() -> DummyClient:
    return DummyClient()


@pytest.fixture()
def gadget(f_client):
    gadget = RemoteLampRGB("test_rgb_lamp",
                           f_client)
    yield gadget
    gadget.__del__()


@pytest.fixture()
def publisher(config: str):
    connector = GadgetPublisherHomekit(config)
    yield connector
    connector.__del__()


@pytest.mark.bridge
def test_gadget_publisher_homekit(publisher: GadgetPublisherHomekit, gadget: Gadget):
    with pytest.raises(GadgetDeletionError):
        publisher.remove_gadget(gadget.name)

    publisher.create_gadget(gadget)

    with pytest.raises(GadgetCreationError):
        publisher.create_gadget(gadget)

    timer = TimingOrganizer()

    print("Awaiting server restart")
    timer.delay(10000)

    publisher.remove_gadget(gadget.name)

    timer.delay(2000)

    publisher.__del__()
