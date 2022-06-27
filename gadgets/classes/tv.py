from abc import abstractmethod, ABC
from typing import Union, List

from gadgets.gadget import Gadget
from gadgets.gadget_update_container import GadgetUpdateContainer


class SourceError(Exception):
    pass


class TvUpdateContainer(GadgetUpdateContainer):
    _status: bool
    _source: bool

    def __init__(self, origin: str):
        super().__init__(origin)
        self._status = False
        self._source = False

    @property
    def status(self) -> bool:
        return self._status

    def set_status(self):
        with self._get_lock():
            self._status = True
            self._record_change()

    @property
    def source(self) -> bool:
        return self._source

    def set_source(self):
        with self._get_lock():
            self._source = True
            self._record_change()


class TV(Gadget, ABC):
    _update_container: TvUpdateContainer

    def __init__(self, name: str):
        super().__init__(name)

    def _get_source_index(self, name: str) -> int:
        for i, s_name in enumerate(self._get_sources()):
            if name == s_name:
                return i
        raise SourceError(f"Unknown Source: {name}")

    def _get_source_name(self, index: int) -> str:
        if index < 0:
            raise SourceError(f"Index is below 0: {index}")
        try:
            return self._get_sources()[index]
        except IndexError:
            raise SourceError(f"Source index too high: {index}")

    @abstractmethod
    def _get_status(self) -> bool:
        pass

    @abstractmethod
    def _set_status(self, value: bool) -> None:
        pass

    @abstractmethod
    def _get_source(self) -> int:
        pass

    @abstractmethod
    def _set_source(self, value: int) -> None:
        pass

    @abstractmethod
    def _get_sources(self) -> list[str]:
        pass

    @property
    def status(self) -> bool:
        return self._get_status()

    @status.setter
    def status(self, value: bool):
        if value != self._get_status():
            self._set_status(value)
            self._logger.info(f"Setting status to {'ON' if value else 'OFF'}")
            self._update_container.set_status()

    @property
    def source(self) -> int:
        return self._get_source()

    @source.setter
    def source(self, value: Union[int, str]):
        if isinstance(value, str):
            value = self._get_source_index(value)
        if value != self._get_source():
            self._set_source(value)
            source_name = self._get_source_name(value)
            self._logger.info(f"Setting source to {source_name}")
            self._update_container.set_source()

    @property
    def source_names(self) -> List[str]:
        return self._get_sources()
