from abc import ABC, abstractmethod

from gadgets.gadget import Gadget
from smarthome_bridge.api_coders.api_encoder_super import ApiEncoderSuper


class GadgetApiEncoder(ApiEncoderSuper, ABC):
    @classmethod
    def encode(cls, obj: Gadget) -> dict:
        """Encodes the local Gadget for the api"""
        return {
            "id": obj.id,
            "is_local": True,
            "attributes": cls._encode_attributes(obj)
        }

    @classmethod
    @abstractmethod
    def _encode_attributes(cls, gadget: Gadget) -> dict:
        """Encodes attributes specific to this gadget"""
