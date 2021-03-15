import enum


class GadgetIdentifier(enum.IntEnum):
    """A number identifier for every gadget type"""
    err_type = 0
    lamp_neopixel_basic = 1
    lamp_basic = 2
    fan_westinghouse_ir = 3
    lamp_westinghouse_ir = 4
    sh_doorbell_basic = 5
    sh_wallswitch_basic = 6
    sh_sensor_motion_hr501 = 7
    sh_sensor_temperature_dht = 8


class CharacteristicIdentifier(enum.IntEnum):
    """A Number for every characteristic"""
    err_type = 0,
    status = 1,
    fanSpeed = 2,
    brightness = 3,
    hue = 4,
    saturation = 5,
    temperature = 6,
    humidity = 7


class CharacteristicUpdateStatus(enum.IntEnum):
    """The return type for the characteristic update"""
    general_error = 0,
    unknown_characteristic = 1,
    update_failed = 2,
    no_update_needed = 3,
    update_successful = 4


def str_to_gadget_ident(g_str: str) -> GadgetIdentifier:
    """Translates a string identifier to a number identifier"""

    switcher = {
        "lamp_neopixel_basic": GadgetIdentifier.lamp_neopixel_basic,
        "lamp_basic": GadgetIdentifier.lamp_basic,
        "fan_westinghouse_ir": GadgetIdentifier.fan_westinghouse_ir,
        "lamp_westinghouse_ir": GadgetIdentifier.lamp_westinghouse_ir,
        "sh_doorbell_basic": GadgetIdentifier.sh_doorbell_basic,
        "sh_wallswitch_basic": GadgetIdentifier.sh_wallswitch_basic,
        "sh_sensor_motion_hr501": GadgetIdentifier.sh_sensor_motion_hr501,
        "sh_sensor_temperature_dht": GadgetIdentifier.sh_sensor_temperature_dht
    }
    return switcher.get(g_str, "None")


def gadget_ident_to_str(ident_str: GadgetIdentifier) -> str:
    switcher = {
        GadgetIdentifier.lamp_neopixel_basic: "lamp_neopixel_basic",
        GadgetIdentifier.lamp_basic: "lamp_basic",
        GadgetIdentifier.fan_westinghouse_ir: "fan_westinghouse_ir",
        GadgetIdentifier.lamp_westinghouse_ir: "lamp_westinghouse_ir",
        GadgetIdentifier.sh_doorbell_basic: "sh_doorbell_basic",
        GadgetIdentifier.sh_wallswitch_basic: "sh_wallswitch_basic",
        GadgetIdentifier.sh_sensor_motion_hr501: "sh_sensor_motion_hr501",
        GadgetIdentifier.sh_sensor_temperature_dht: "sh_sensor_temperature_dht"
    }
    return switcher.get(ident_str, "None")


class GadgetMethod(enum.Enum):
    """A number identifier for every gadget method"""

    err_type = 0
    turnOn = 1
    turnOff = 2
    toggleStatus = 3
    brightnessUp = 4
    brightnessDown = 5
    volumeUp = 6
    volumeDown = 7
    mute = 8
    unmute = 9
    toggleMute = 10
    mode0 = 11
    mode1 = 12
    mode2 = 13
    mode3 = 14
    mode4 = 15
    modeUp = 16
    modeDown = 17


def str_to_gadget_method(g_str: str) -> GadgetMethod:
    """Translates a string identifier to a number identifier"""

    switcher = {
        "turnOn": GadgetMethod.turnOn,
        "turnOff": GadgetMethod.turnOff,
        "toggleStatus": GadgetMethod.toggleStatus,
        "brightnessUp": GadgetMethod.brightnessUp,
        "brightnessDown": GadgetMethod.brightnessDown,
        "volumeUp": GadgetMethod.volumeUp,
        "volumeDown": GadgetMethod.volumeDown,
        "mute": GadgetMethod.mute,
        "unmute": GadgetMethod.unmute,
        "toggleMute": GadgetMethod.toggleMute,
        "mode0": GadgetMethod.mode0,
        "mode1": GadgetMethod.mode1,
        "mode2": GadgetMethod.mode2,
        "mode3": GadgetMethod.mode3,
        "mode4": GadgetMethod.mode4,
        "modeUp": GadgetMethod.modeUp,
        "modeDown": GadgetMethod.modeDown

    }
    return switcher.get(g_str, "None")


def characteristic_ident_to_str(characteristic: CharacteristicIdentifier) -> str:
    switcher = {
        CharacteristicIdentifier.err_type: "err",
        CharacteristicIdentifier.status: "status",
        CharacteristicIdentifier.fanSpeed: "fanSpeed",
        CharacteristicIdentifier.brightness: "brightness",
        CharacteristicIdentifier.hue: "hue",
        CharacteristicIdentifier.saturation: "saturation",
        CharacteristicIdentifier.temperature: "temperature",
        CharacteristicIdentifier.humidity: "humidity"
    }
    return switcher.get(characteristic, "err")


if __name__ == '__main__':
    for ident in GadgetIdentifier:
        print(ident)

    for method in GadgetMethod:
        print(method)
