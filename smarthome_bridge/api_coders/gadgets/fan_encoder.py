from gadgets.remote.fan import Fan
from smarthome_bridge.api_coders.remote_gadget_api_encoder import RemoteGadgetApiEncoder


class FanEncoder(RemoteGadgetApiEncoder):
    @classmethod
    def _encode_attributes(cls, gadget: Fan) -> dict:
        return {
            "speed": gadget.speed,
            "steps": gadget.steps
        }
