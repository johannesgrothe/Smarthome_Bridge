from abc import ABC

from gadgets.i_updatable_gadget import IUpdatableGadget


class ILocalGadget(IUpdatableGadget, ABC):
    pass
