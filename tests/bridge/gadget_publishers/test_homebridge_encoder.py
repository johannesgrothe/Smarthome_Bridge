import pytest

from gadget_publishers.homebridge_encoder import HomebridgeEncoder, GadgetEncodeError
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier

from gadgets.any_gadget import AnyGadget
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from gadgets.fan_westinghouse_ir import FanWestinghouseIR


TEST_CLIENT = "test_client"


L_NAME = "test_lamp"
L_CHARACTERISTIC_MIN = 0

L_STATUS_MAX = 1
L_BRIGHTNESS_MAX = 100
L_HUE_MAX = 255
L_SATURATION_MAX = 100

L_RESULT = {
    "name": L_NAME,
    "service_name": L_NAME,
    "service": "Lightbulb",
    "On": {"minValue": L_CHARACTERISTIC_MIN, "maxValue": L_STATUS_MAX, "minStep": 1},
    "Brightness": {"minValue": L_CHARACTERISTIC_MIN, "maxValue": L_BRIGHTNESS_MAX, "minStep": 1},
    "Hue": {"minValue": L_CHARACTERISTIC_MIN, "maxValue": L_HUE_MAX, "minStep": 1},
    "Saturation": {"minValue": L_CHARACTERISTIC_MIN, "maxValue": L_SATURATION_MAX, "minStep": 1}
}

ANY_NAME = "test_any_gadget"

FAN_NAME = "test_fan"
FAN_SPEED_MIN = 0
FAN_SPEED_MAX = 100
FAN_SPEED_STEPS = 3

FAN_RESULT = {
    "name": FAN_NAME,
    "service_name": FAN_NAME,
    "service": "Fan",
    "On": {"minValue": L_CHARACTERISTIC_MIN, "maxValue": L_STATUS_MAX, "minStep": 1},
    "RotationSpeed": {"minValue": FAN_SPEED_MIN, "maxValue": FAN_SPEED_MAX, "minStep": 33}
}


@pytest.fixture()
def encoder():
    encoder = HomebridgeEncoder()
    yield encoder


@pytest.fixture()
def characteristic_status():
    status = Characteristic(c_type=CharacteristicIdentifier.status,
                            min_val=L_CHARACTERISTIC_MIN,
                            max_val=L_STATUS_MAX)
    yield status


@pytest.fixture()
def any_gadget(characteristic_status):
    gadget = AnyGadget(ANY_NAME,
                       TEST_CLIENT,
                       [characteristic_status])
    yield gadget
    gadget.__del__()


@pytest.fixture()
def lamp(characteristic_status):
    lamp = LampNeopixelBasic(L_NAME,
                             TEST_CLIENT,
                             characteristic_status,
                             Characteristic(c_type=CharacteristicIdentifier.brightness,
                                            min_val=L_CHARACTERISTIC_MIN,
                                            max_val=L_BRIGHTNESS_MAX),
                             Characteristic(c_type=CharacteristicIdentifier.hue,
                                            min_val=L_CHARACTERISTIC_MIN,
                                            max_val=L_HUE_MAX),
                             Characteristic(c_type=CharacteristicIdentifier.saturation,
                                            min_val=L_CHARACTERISTIC_MIN,
                                            max_val=L_SATURATION_MAX)
                             )
    yield lamp
    lamp.__del__()


@pytest.fixture()
def fan(characteristic_status):
    fan = FanWestinghouseIR(FAN_NAME,
                            TEST_CLIENT,
                            characteristic_status,
                            Characteristic(c_type=CharacteristicIdentifier.fan_speed,
                                           min_val=FAN_SPEED_MIN,
                                           max_val=FAN_SPEED_MAX,
                                           steps=FAN_SPEED_STEPS)
                            )
    yield fan
    fan.__del__()


@pytest.mark.bridge
def test_homebridge_decoder_error(encoder: HomebridgeEncoder, any_gadget: AnyGadget):
    with pytest.raises(GadgetEncodeError):
        encoder.encode_gadget(any_gadget)


@pytest.mark.bridge
def test_homebridge_decoder_lamp(encoder: HomebridgeEncoder, lamp: LampNeopixelBasic):
    assert encoder.encode_gadget(lamp) == L_RESULT


@pytest.mark.bridge
def test_homebridge_decoder_fan(encoder: HomebridgeEncoder, fan: FanWestinghouseIR):
    assert encoder.encode_gadget(fan) == FAN_RESULT
