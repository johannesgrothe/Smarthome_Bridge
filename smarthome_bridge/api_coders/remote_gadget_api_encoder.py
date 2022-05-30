from abc import abstractmethod, ABC

from gadgets.local.local_gadget import LocalGadget
from gadgets.remote.remote_gadget import RemoteGadget
from smarthome_bridge.api_coders.gadget_api_encoder import GadgetApiEncoder


class RemoteGadgetApiEncoder(GadgetApiEncoder, ABC):
    @classmethod
    def encode(cls, obj: RemoteGadget) -> dict:
        """Encodes the local Gadget for the api"""
        data = super().encode(obj)
        data["host_client"] = obj.host_client
        data["is_local"] = False
        return data
