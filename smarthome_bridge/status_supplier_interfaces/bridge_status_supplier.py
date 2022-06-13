from abc import ABCMeta, abstractmethod

from smarthome_bridge.bridge_information_container import BridgeInformationContainer


class BridgeStatusSupplier(metaclass=ABCMeta):

    @abstractmethod
    @property
    def info(self) -> BridgeInformationContainer:
        pass
