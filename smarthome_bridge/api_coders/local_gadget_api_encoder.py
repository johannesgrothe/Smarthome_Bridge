from abc import abstractmethod, ABC

from gadgets.local.local_gadget import LocalGadget
from smarthome_bridge.api_coders.gadget_api_encoder import GadgetApiEncoder


class LocalGadgetApiEncoder(GadgetApiEncoder, ABC):
    @classmethod
    def encode(cls, obj: LocalGadget) -> dict:
        """Encodes the local Gadget for the api"""
        return super().encode(obj)
