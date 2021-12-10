from abc import ABCMeta, abstractmethod
from typing import Optional

from gadgets.gadget import Gadget


class GadgetStatusSupplier(metaclass=ABCMeta):
    @abstractmethod
    def get_gadget(self, name: str) -> Optional[Gadget]:
        pass
