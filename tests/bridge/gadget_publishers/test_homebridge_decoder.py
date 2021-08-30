import pytest

from gadget_publishers.homebridge_decoder import HomebridgeDecoder
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier

HOMEBRIDGE_RESPONSE = {
    "test_fan": {
        "services": {
            "test_fan": "Fan"
        },
        "characteristics": {
            "test_fan": {
                "On": True,
                "RotationSpeed": 33
            }
        },
        "properties": {
            "test_fan": {
                "On": {
                    "format": "bool",
                    "unit": None,
                    "minValue": 0,
                    "maxValue": 1,
                    "minStep": 1,
                    "perms": ["pr", "pw", "ev"]
                },
                "RotationSpeed": {
                    "format": "float",
                    "unit": "percentage",
                    "minValue": 0,
                    "maxValue": 100,
                    "minStep": 33,
                    "perms": ["pr", "pw", "ev"]
                }
            }
        }
    },
    "request_id": 0
}


@pytest.fixture()
def fan_speed_characteristic():
    fan_speed = Characteristic(CharacteristicIdentifier.fanSpeed,
                               0,
                               100,
                               3,
                               1)
    yield fan_speed


@pytest.fixture()
def status_characteristic():
    status = Characteristic(CharacteristicIdentifier.status,
                            0,
                            1,
                            1,
                            1)
    yield status


@pytest.fixture()
def gadget_json():
    return HOMEBRIDGE_RESPONSE["test_fan"]


@pytest.fixture()
def decoder():
    return HomebridgeDecoder()


@pytest.mark.bridge
def test_homebridge_encoder(decoder: HomebridgeDecoder, fan_speed_characteristic: Characteristic,
                            status_characteristic: Characteristic, gadget_json: dict):
    characteristic_list = decoder.decode_characteristics(gadget_json)
    compare_list = [fan_speed_characteristic, status_characteristic]
    compare_list.sort()
    assert characteristic_list == compare_list
