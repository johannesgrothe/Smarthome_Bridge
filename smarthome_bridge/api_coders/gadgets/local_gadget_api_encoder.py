from abc import ABC

from gadgets.local.local_gadget import LocalGadget
from smarthome_bridge.api_coders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper


class LocalGadgetApiEncoderSuper(GadgetApiEncoderSuper, ABC):
    @classmethod
    def encode_gadget(cls, gadget: LocalGadget) -> dict:
        """Encodes the local Gadget for the api"""
        return super().encode_gadget(gadget)
