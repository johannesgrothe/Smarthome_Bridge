from abc import abstractmethod, ABCMeta


class IUpdateContainer(metaclass=ABCMeta):

    @abstractmethod
    def _record_change(self):
        pass

    @abstractmethod
    def _get_last_change(self):
        pass

    @abstractmethod
    def _get_lock(self):
        pass
