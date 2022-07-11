from gadgets.classes.tv import SourceError
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from smarthome_bridge.gadget_update_appliers.gadget_update_applier_super import GadgetUpdateApplierSuper, \
    UpdateApplyError


class UpdateApplierDenonRemoteControl(GadgetUpdateApplierSuper):
    @classmethod
    def get_schema(cls) -> str:
        return "api_gadget_update_denon"

    @classmethod
    def _apply_update(cls, gadget: DenonRemoteControlGadget, update_data: dict) -> None:
        if "source" in update_data:
            new_source = update_data["source"]
            try:
                gadget.source = new_source
            except SourceError:
                raise UpdateApplyError(f"Cannot apply source '{new_source}' to gadget '{gadget.id}'")

        if "status" in update_data:
            new_status = update_data["status"]
            gadget.status = new_status
