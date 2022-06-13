from typing import List, Tuple, Type

from gadgets.gadget import Gadget
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from smarthome_bridge.gadget_update_appliers.gadget_update_applier_super import GadgetUpdateApplierSuper, \
    UpdateApplyError
from smarthome_bridge.gadget_update_appliers.update_applier_denon_remote_control import UpdateApplierDenonRemoteControl

_type_mapping: List[Tuple[Type[Gadget], Type[GadgetUpdateApplierSuper]]] = [
    (DenonRemoteControlGadget, UpdateApplierDenonRemoteControl)
]


class GadgetUpdateApplier:

    @classmethod
    def apply(cls, gadget: Gadget, update_data: dict) -> None:
        """
        Applies update data to a gadget

        :param gadget: Gadget to apply the update to
        :param update_data: Dictionary containing the update data
        :return: None
        :raises UpdateApplyError: If anything goes wrong for any reason
        :raises ValidationError: If data is badly formatted
        """
        for gadget_type, encoder_type in _type_mapping:
            if isinstance(gadget, gadget_type):
                encoder_type.apply_update(gadget, update_data)
                return
        raise UpdateApplyError(gadget.__class__.__name__, gadget.name, "No encoder found")
