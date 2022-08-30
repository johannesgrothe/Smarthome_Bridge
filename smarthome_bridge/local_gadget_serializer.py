from gadgets.gadget import Gadget
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.i_local_gadget import ILocalGadget
from system.gadget_definitions import LocalGadgetIdentifier


class LocalGadgetSerializer:

    @staticmethod
    def _serialize_denon_avr(gadget: DenonRemoteControlGadget) -> dict:
        return {
            "ip": gadget.address
        }

    @classmethod
    def serialize(cls, gadget: ILocalGadget) -> dict:
        if not isinstance(gadget, Gadget):
            raise TypeError()
        data = {"id": gadget.id,
                "name": gadget.name,
                "type": None}
        if isinstance(gadget, DenonRemoteControlGadget):
            data["type"] = LocalGadgetIdentifier.denon_av_receiver.value
            data |= cls._serialize_denon_avr(gadget)

        return data
