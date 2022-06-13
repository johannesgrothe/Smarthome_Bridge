from typing import Type, Tuple, List

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.local_gadget import LocalGadget
from gadgets.remote.remote_gadget import RemoteGadget
from lib.logging_interface import ILogging
from smarthome_bridge.api_coders.gadgets.encoders.denon_receiver_encoder import DenonReceiverEncoder
from smarthome_bridge.api_coders.gadgets.gadget_api_encoder_super import GadgetApiEncoderSuper

_type_mapping: List[Tuple[Type[Gadget], Type[GadgetApiEncoderSuper]]] = [
    (DenonRemoteControlGadget, DenonReceiverEncoder)
]


class GadgetEncodeError(Exception):
    def __init__(self, class_name: str, gadget_name: str, reason: str = "unknown"):
        super().__init__(f"Cannot encode {class_name} '{gadget_name}' because: {reason}")


class GadgetApiEncoder(ILogging):
    @classmethod
    def encode_gadget(cls, gadget: Gadget) -> dict:
        for gadget_type, encoder_type in _type_mapping:
            if isinstance(gadget, gadget_type):
                return encoder_type.encode_gadget(gadget)
        raise GadgetEncodeError(gadget.__class__.__name__, gadget.name, "No encoder found")

    @classmethod
    def encode_gadget_update(cls, container: GadgetUpdateContainer, gadget: Gadget) -> dict:
        for gadget_type, encoder_type in _type_mapping:
            if isinstance(gadget, gadget_type):
                return encoder_type.encode_gadget_update(gadget, container)
        raise GadgetEncodeError(gadget.__class__.__name__, gadget.name, "No encoder found")

    @classmethod
    def encode_all_gadgets_info(cls, remote_gadgets: list[RemoteGadget], local_gadgets: list[LocalGadget]) -> dict:
        remote_gadget_data = []
        for gadget in remote_gadgets:
            try:
                remote_gadget_data.append(cls.encode_gadget(gadget))
            except GadgetEncodeError as err:
                cls._get_logger().error(err.args[0])

        local_gadget_data = []
        for gadget in local_gadgets:
            try:
                local_gadget_data.append(cls.encode_gadget(gadget))
            except GadgetEncodeError as err:
                cls._get_logger().error(err.args[0])

        return {"remote": remote_gadget_data,
                "local": local_gadget_data}
