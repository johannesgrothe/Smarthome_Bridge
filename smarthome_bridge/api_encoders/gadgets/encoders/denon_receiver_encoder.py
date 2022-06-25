from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget, DenonRemoteControlGadgetUpdateContainer
from smarthome_bridge.api_encoders.gadgets.local_gadget_api_encoder import LocalGadgetApiEncoderSuper
from system.gadget_definitions import GadgetClass


class DenonReceiverEncoder(LocalGadgetApiEncoderSuper):
    @classmethod
    def _encode_class(cls) -> GadgetClass:
        return GadgetClass.tv

    @classmethod
    def _encode_update_attributes(cls, gadget: DenonRemoteControlGadget,
                                  container: DenonRemoteControlGadgetUpdateContainer) -> dict:
        out_data = {}
        if container.name:
            out_data["name"] = gadget.name
        if container.status:
            out_data["status"] = gadget.status
        if container.source:
            out_data["source"] = gadget.source
        return out_data

    @classmethod
    def _encode_attributes(cls, gadget: DenonRemoteControlGadget) -> dict:
        return {
            "status": gadget.status,
            "source": gadget.source_names[gadget.source],
            "sources": gadget.source_names
        }
