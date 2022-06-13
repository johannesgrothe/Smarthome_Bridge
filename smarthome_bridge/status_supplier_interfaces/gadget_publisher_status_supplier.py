from abc import ABCMeta, abstractmethod
from typing import List

from gadget_publishers.gadget_publisher import GadgetPublisher


class GadgetPublisherStatusSupplier(metaclass=ABCMeta):

    @property
    def publishers(self) -> List[GadgetPublisher]:
        return self._get_publishers()

    @abstractmethod
    def _get_publishers(self) -> List[GadgetPublisher]:
        pass
