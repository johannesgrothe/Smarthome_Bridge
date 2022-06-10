from abc import abstractmethod, ABCMeta

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer


class GadgetApiEncoderSuper(metaclass=ABCMeta):
    @classmethod
    def encode_gadget(cls, gadget: Gadget) -> dict:
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

    @classmethod
    @abstractmethod
    def encode_gadget_update(cls, gadget: Gadget, container: GadgetUpdateContainer) -> dict:
        """Encodes the local Gadget for the api"""
