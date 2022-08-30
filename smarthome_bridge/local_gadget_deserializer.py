from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.i_local_gadget import ILocalGadget
from system.gadget_definitions import LocalGadgetIdentifier


class LocalGadgetDeserializer:

    @staticmethod
    def _deserialize_denon_avr(data: dict) -> DenonRemoteControlGadget:
        return DenonRemoteControlGadget(data["name"], data["ip"])

    @classmethod
    def deserialize(cls, data: dict) -> ILocalGadget:
        if data["type"] == LocalGadgetIdentifier.denon_av_receiver.value:
            return cls._deserialize_denon_avr(data)
