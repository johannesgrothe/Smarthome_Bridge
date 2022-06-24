from abc import ABC

from gadgets.remote.remote_gadget import RemoteGadget
from smarthome_bridge.api_encoders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper
from smarthome_bridge.client_information_interface import ClientInformationInterface


class RemoteGadgetApiEncoderSuper(GadgetApiEncoderSuper, ABC):
    @classmethod
    def encode_gadget(cls, gadget: RemoteGadget) -> dict:
        """Encodes the local Gadget for the api"""
        data = super().encode_gadget(gadget)
        data["host_client"] = cls._encode_host(gadget.host_client)
        data["is_local"] = False
        return data

    @classmethod
    def _encode_host(cls, host: ClientInformationInterface) -> dict:
        return {
            "id": host.id,
            "is_active": host.is_active
        }
