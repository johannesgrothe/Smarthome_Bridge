from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.remote.fan import Fan, FanUpdateContainer
from smarthome_bridge.api_encoders.gadgets.remote_gadget_api_encoder import RemoteGadgetApiEncoderSuper


class FanEncoder(RemoteGadgetApiEncoderSuper):
    @classmethod
    def _encode_update_attributes(cls, gadget: Fan, container: FanUpdateContainer) -> dict:
        out_data = {}
        if container.name:
            out_data["name"] = gadget.name
        if container.speed:
            out_data["speed"] = gadget.speed
        return out_data

    @classmethod
    def _encode_attributes(cls, gadget: Fan) -> dict:
        return {
            "speed": gadget.speed,
            "steps": gadget.steps
        }
