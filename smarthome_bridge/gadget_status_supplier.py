from abc import ABCMeta, abstractmethod
from typing import Optional

from gadgets.remote_gadget import RemoteGadget


class GadgetStatusSupplier(metaclass=ABCMeta):
    @abstractmethod
    def get_gadget(self, name: str) -> Optional[RemoteGadget]:
        pass
