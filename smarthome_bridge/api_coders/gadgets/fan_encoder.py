from gadgets.remote.fan import Fan, FanUpdateContainer
from smarthome_bridge.api_coders.gadgets.remote_gadget_api_encoder import RemoteGadgetApiEncoderSuper


class FanEncoder(RemoteGadgetApiEncoderSuper):
    @classmethod
    def encode_gadget_update(cls, gadget: Fan, container: FanUpdateContainer) -> dict:
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
