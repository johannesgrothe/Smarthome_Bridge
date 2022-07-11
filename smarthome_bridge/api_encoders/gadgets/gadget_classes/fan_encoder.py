from gadgets.remote.remote_fan import Fan, FanUpdateContainer
from smarthome_bridge.api_encoders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper
from system.gadget_definitions import GadgetClass


class FanEncoder(GadgetApiEncoderSuper):
    @classmethod
    def _encode_class(cls) -> GadgetClass:
        return GadgetClass.fan

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
