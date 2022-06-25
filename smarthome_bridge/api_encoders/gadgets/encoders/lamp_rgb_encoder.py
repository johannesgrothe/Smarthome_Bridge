from gadgets.remote.lamp_rgb import LampRGB, LampRgbUpdateContainer
from smarthome_bridge.api_encoders.gadgets.remote_gadget_api_encoder import RemoteGadgetApiEncoderSuper
from system.gadget_definitions import GadgetClass


class LampRgbEncoder(RemoteGadgetApiEncoderSuper):
    @classmethod
    def _encode_class(cls) -> GadgetClass:
        return GadgetClass.lamp_rgb

    @classmethod
    def _encode_update_attributes(cls, gadget: LampRGB, container: LampRgbUpdateContainer) -> dict:
        out_data = {}
        if container.rgb:
            out_data["red"] = gadget.red,
            out_data["green"] = gadget.green,
            out_data["blue"] = gadget.blue
        return out_data

    @classmethod
    def _encode_attributes(cls, gadget: LampRGB) -> dict:
        return {
            "red": gadget.red,
            "green": gadget.green,
            "blue": gadget.blue
        }
