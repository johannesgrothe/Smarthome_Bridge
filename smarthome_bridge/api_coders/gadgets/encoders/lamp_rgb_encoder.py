from gadgets.remote.lamp_rgb import LampRGB
from smarthome_bridge.api_coders.gadgets.remote_gadget_api_encoder import RemoteGadgetApiEncoderSuper


class LampRgbEncoder(RemoteGadgetApiEncoderSuper):
    @classmethod
    def _encode_attributes(cls, gadget: LampRGB) -> dict:
        return {
            "red": gadget.red,
            "green": gadget.green,
            "blue": gadget.blue
        }
