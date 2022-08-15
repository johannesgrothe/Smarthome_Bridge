from abc import ABC

from gadgets.local.i_local_gadget import ILocalGadget
from smarthome_bridge.api_encoders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper


class ILocalGadgetApiEncoder(GadgetApiEncoderSuper, ABC):

    @classmethod
    def encode_host_attributes(cls, gadget: ILocalGadget) -> dict:
        data = {"is_local": True}
        return data
