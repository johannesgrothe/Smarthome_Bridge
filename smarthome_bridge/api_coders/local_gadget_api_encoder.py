from abc import abstractmethod

from local_gadgets.local_gadget import LocalGadget
from smarthome_bridge.api_coders.gadget_api_encoder import GadgetApiEncoder


class LocalGadgetApiEncoder(GadgetApiEncoder):
    @classmethod
    def encode(cls, obj: LocalGadget) -> dict:
        """Encodes the local Gadget for the api"""
        return {
            "id": obj.id,
            "attributes": cls._encode_attributes(obj)
        }

    @classmethod
    @abstractmethod
    def _encode_attributes(cls, gadget: LocalGadget) -> dict:
        """Encodes attributes specific to this gadget"""
