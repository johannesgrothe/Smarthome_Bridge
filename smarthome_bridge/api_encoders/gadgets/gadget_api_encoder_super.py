from abc import abstractmethod, ABCMeta

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from system.gadget_definitions import GadgetClass


class GadgetApiEncoderSuper(metaclass=ABCMeta):
    @classmethod
    def encode_gadget(cls, gadget: Gadget) -> dict:
        """Encodes the local Gadget for the api"""
        return {
            "id": gadget.id,
            "is_local": True,
            "class": cls._encode_class().value,
            "attributes": cls._encode_attributes(gadget)
        }

    @classmethod
    @abstractmethod
    def _encode_class(cls) -> GadgetClass:
        """Encodes the class of the gadget"""

    @classmethod
    @abstractmethod
    def _encode_attributes(cls, gadget: Gadget) -> dict:
        """Encodes attributes specific to this gadget"""

    @classmethod
    def encode_gadget_update(cls, gadget: Gadget, container: GadgetUpdateContainer) -> dict:
        """Encodes the update data for the api"""
        data = {
            "id": gadget.id,
            "attributes": cls._encode_update_attributes(gadget, container)
        }

        if container.name:
            data["name"] = gadget.name

        return data

    @classmethod
    @abstractmethod
    def _encode_update_attributes(cls, gadget: Gadget, container: GadgetUpdateContainer) -> dict:
        """Encodes update data fpr the gadgets attributes"""
