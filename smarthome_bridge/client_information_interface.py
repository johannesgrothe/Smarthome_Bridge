from abc import abstractmethod, ABCMeta


class ClientInformationInterface(metaclass=ABCMeta):
    @property
    def is_active(self) -> bool:
        return self._is_active()

    @abstractmethod
    def _is_active(self) -> bool:
        pass

    @property
    def id(self) -> str:
        return self._get_id()

    @abstractmethod
    def _get_id(self) -> str:
        pass
