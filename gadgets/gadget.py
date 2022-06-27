import logging
from abc import ABC

from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.i_updatable_gadget import IUpdatableGadget


class Gadget(IUpdatableGadget, ABC):
    _id: str
    _name: str
    _logger: logging.Logger

    def __init__(self,
                 gadget_id: str):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._id = gadget_id
        self._name = self._id
        self.reset_updated_properties()

    def __del__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if not self._name == value:
            self._name = value
            self._update_container.set_name()

    @property
    def updated_properties(self) -> GadgetUpdateContainer:
        return self._update_container
