from gadgets.classes.tv import TvUpdateContainer, TV
from smarthome_bridge.api_encoders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper
from system.gadget_definitions import GadgetClass


class TvEncoder(GadgetApiEncoderSuper):
    @classmethod
    def _encode_class(cls) -> GadgetClass:
        return GadgetClass.tv

    @classmethod
    def _encode_update_attributes(cls, gadget: TV,
                                  container: TvUpdateContainer) -> dict:
        out_data = {}
        if container.name:
            out_data["name"] = gadget.name
        if container.status:
            out_data["status"] = gadget.status
        if container.source:
            out_data["source"] = gadget.source
        return out_data

    @classmethod
    def _encode_attributes(cls, gadget: TV) -> dict:
        return {
            "status": gadget.status,
            "source": gadget.source_names[gadget.source],
            "sources": gadget.source_names
        }
