from abc import ABCMeta, abstractmethod
from typing import List

from gadget_publishers.gadget_publisher import GadgetPublisher


class GadgetPublisherStatusSupplier(metaclass=ABCMeta):

    @abstractmethod
    @property
    def publishers(self) -> List[GadgetPublisher]:
        pass
