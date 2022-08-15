from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget, DenonRemoteControlGadgetUpdateContainer
from smarthome_bridge.api_encoders.gadgets.gadget_classes.tv_encoder import TvEncoder
from smarthome_bridge.api_encoders.gadgets.i_local_gadget_api_encoder import ILocalGadgetApiEncoder


class LocalTvEncoder(TvEncoder, ILocalGadgetApiEncoder):

    @classmethod
    def encode_gadget(cls, gadget: DenonRemoteControlGadget) -> dict:
        return {**super().encode_gadget(gadget), **cls.encode_host_attributes(gadget)}
