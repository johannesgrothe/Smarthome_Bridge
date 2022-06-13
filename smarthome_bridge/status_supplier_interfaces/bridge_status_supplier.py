from abc import ABCMeta, abstractmethod

from smarthome_bridge.bridge_information_container import BridgeInformationContainer


class BridgeStatusSupplier(metaclass=ABCMeta):

    @property
    def info(self) -> BridgeInformationContainer:
        return self._get_info()

    @abstractmethod
    def _get_info(self) -> BridgeInformationContainer:
        pass
