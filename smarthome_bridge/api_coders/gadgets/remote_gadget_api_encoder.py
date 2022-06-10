from abc import ABC

from gadgets.remote.remote_gadget import RemoteGadget
from smarthome_bridge.api_coders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper


class RemoteGadgetApiEncoderSuper(GadgetApiEncoderSuper, ABC):
    @classmethod
    def encode_gadget(cls, obj: RemoteGadget) -> dict:
        """Encodes the local Gadget for the api"""
        data = super().encode_gadget(obj)
        data["host_client"] = obj.host_client
        data["is_local"] = False
        return data
