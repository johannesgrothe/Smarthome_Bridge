import datetime
import threading


class GadgetUpdateContainer:
    _lock: threading.Lock
    _source_id: str
    _last_changed: datetime.datetime
    _name: bool

    def __init__(self, origin_id: str):
        self._source_id = origin_id
        self._lock = threading.Lock()
        self._name = False
        self._last_changed = datetime.datetime.now()

    def _record_change(self):
        with self._lock:
            self._last_changed = datetime.datetime.now()

    @property
    def origin(self) -> str:
        with self._lock:
            return self._source_id

    @property
    def last_changed(self) -> datetime.datetime:
        with self._lock:
            return self._last_changed

    @property
    def is_empty(self):
        with self._lock:
            is_empty = True
            for key, value in self.__dict__.items():
                if key not in []:
                    is_empty &= value
            return is_empty

    @property
    def name(self) -> bool:
        return self._name

    def set_name(self):
        with self._lock:
            self._name = True
            self._record_change()
