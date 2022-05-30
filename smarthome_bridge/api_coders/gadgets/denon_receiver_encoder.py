from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from smarthome_bridge.api_coders.local_gadget_api_encoder import LocalGadgetApiEncoder


class DenonReceiverEncoder(LocalGadgetApiEncoder):
    @classmethod
    def _encode_attributes(cls, gadget: DenonRemoteControlGadget) -> dict:
        return {
            "status": gadget.status,
            "source": gadget.source_names[gadget.source],
            "sources": gadget.source_names
        }
