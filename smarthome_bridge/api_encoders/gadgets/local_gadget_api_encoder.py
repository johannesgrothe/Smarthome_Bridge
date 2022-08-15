from abc import ABC

from gadgets.local.i_local_gadget import ILocalGadget
from smarthome_bridge.api_encoders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper


class LocalGadgetApiEncoderSuper(GadgetApiEncoderSuper, ABC):
    @classmethod
    def encode_gadget(cls, gadget: ILocalGadget) -> dict:
        """Encodes the local Gadget for the api"""
        return super().encode_gadget(gadget)
