from abc import ABC

from gadgets.gadget import Gadget


class LocalGadget(Gadget, ABC):

    def __init__(self, gadget_id: str):
        super().__init__(gadget_id)
