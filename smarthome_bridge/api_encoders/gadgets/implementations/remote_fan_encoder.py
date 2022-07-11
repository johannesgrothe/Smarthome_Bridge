from gadgets.remote.remote_fan import RemoteFan
from smarthome_bridge.api_encoders.gadgets.gadget_classes.fan_encoder import FanEncoder
from smarthome_bridge.api_encoders.gadgets.i_remote_gadget_api_encoder import IRemoteGadgetApiEncoder


class RemoteFanEncoder(FanEncoder, IRemoteGadgetApiEncoder):
    @classmethod
    def encode_gadget(cls, gadget: RemoteFan) -> dict:
        return {**super().encode_gadget(gadget), **cls.encode_host_attributes(gadget)}
