import datetime
import threading

from gadgets.i_update_container import IUpdateContainer


class GadgetUpdateContainer(IUpdateContainer):
    __lock: threading.Lock
    __last_changed: datetime.datetime
    _source_id: str
    _name: bool

    def __init__(self, origin_id: str):
        super().__init__()
        self.__lock = threading.Lock()
        self.__last_changed = datetime.datetime.now()
        self._source_id = origin_id
        self._name = False

    def _get_lock(self):
        return self.__lock

    def _record_change(self):
        self.__last_changed = datetime.datetime.now()

    def _get_last_change(self):
        return self.__last_changed

    @property
    def origin(self) -> str:
        with self._get_lock():
            return self._source_id

    @property
    def last_changed(self) -> datetime.datetime:
        with self._get_lock():
            return self.__last_changed

    @property
    def is_empty(self) -> bool:
        with self._get_lock():
            is_empty = True
            for key, value in self.__dict__.items():
                if not key.startswith("_GadgetUpdateContainer") and key not in ["__lock", "_source_id",
                                                                                "__last_changed"]:
                    is_empty &= not value
            return is_empty

    @property
    def name(self) -> bool:
        return self._name

    def set_name(self):
        with self._get_lock():
            self._name = True
            self._record_change()
