from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from smarthome_bridge.api_encoders.gadgets.gadget_classes.lamp_rgb_encoder import LampRgbEncoder
from smarthome_bridge.api_encoders.gadgets.i_remote_gadget_api_encoder import IRemoteGadgetApiEncoder


class RemoteLampRgbEncoder(LampRgbEncoder, IRemoteGadgetApiEncoder):
    @classmethod
    def encode_gadget(cls, gadget: RemoteLampRGB) -> dict:
        return {**super().encode_gadget(gadget), **cls.encode_host_attributes(gadget)}
