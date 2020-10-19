import enum


class GadgetIdentifier(enum.Enum):
    """An number identifier for every gadget type"""

    err_type = 0
    lamp_neopixel_basic = 1
    lamp_basic = 2
    fan_westinghouse_ir = 3
    lamp_westinghouse_ir = 4


def str_to_gadget_ident(g_str: str) -> GadgetIdentifier:
    """Translates a string identifier to a number identifier"""

    switcher = {
        "lamp_neopixel_basic": GadgetIdentifier.lamp_neopixel_basic,
        "lamp_basic": GadgetIdentifier.lamp_basic,
        "fan_westinghouse_ir": GadgetIdentifier.fan_westinghouse_ir,
        "lamp_westinghouse_ir": GadgetIdentifier.lamp_westinghouse_ir
    }
    return switcher.get(g_str, "None")


if __name__ == '__main__':
    for ident in GadgetIdentifier:
        print(ident)

    print()

    print(str_to_gadget_ident("lamp_basic"))
