from typing import Optional

from gadgets.gadget import Gadget
from smarthome_bridge.gadget_update_appliers.gadget_update_applier import GadgetUpdateApplier


class DummyGadgetUpdateApplier(GadgetUpdateApplier):
    mock_exception: Optional[Exception]

    def __init__(self):
        self.mock_exception = None

    def apply(self, gadget: Gadget, update_data: dict) -> None:
        if self.mock_exception is not None:
            raise self.mock_exception
