import pytest
from homekit.model import Accessory

from gadget_publishers.homekit.homekit_accessory_rgb_lamp import HomekitRGBLamp
from test_helpers.dummy_homekit_update_receiver import DummyHomekitUpdateReceiver

LAMP_NAME = "dummy_lamp"


@pytest.fixture()
def update_receiver():
    buf = DummyHomekitUpdateReceiver()
    yield buf


@pytest.fixture()
def lamp(update_receiver: DummyHomekitUpdateReceiver):
    lamp = HomekitRGBLamp(LAMP_NAME,
                          update_receiver,
                          0,
                          55,
                          66,
                          77)
    yield lamp


@pytest.mark.bridge
def test_homekit_rgb_lamp(lamp: HomekitRGBLamp, update_receiver: DummyHomekitUpdateReceiver):
    assert lamp.name == LAMP_NAME
    assert isinstance(lamp.accessory, Accessory)

    assert lamp.status == 0
    assert lamp.hue == 55
    assert lamp.brightness == 66
    assert lamp.saturation == 77

    assert update_receiver.last_update is None

    lamp.status = 1
    assert update_receiver.last_update is not None
    name, data = update_receiver.last_update
    assert name == LAMP_NAME
    assert data["status"] == 1

    update_receiver.last_update = None
    lamp.hue = 30
    assert update_receiver.last_update is not None
    _, data = update_receiver.last_update
    assert data["hue"] == 30

    update_receiver.last_update = None
    lamp.brightness = 40
    assert update_receiver.last_update is not None
    _, data = update_receiver.last_update
    assert data["brightness"] == 40

    update_receiver.last_update = None
    lamp.saturation = 50
    assert update_receiver.last_update is not None
    _, data = update_receiver.last_update
    assert data["saturation"] == 50
