from abc import ABCMeta, abstractmethod

from gadgets.gadget_update_container import GadgetUpdateContainer


class IUpdatableGadget(metaclass=ABCMeta):
    _update_container: GadgetUpdateContainer

    @property
    def updated_properties(self) -> GadgetUpdateContainer:
        return self._update_container

    @abstractmethod
    def reset_updated_properties(self):
        pass
