from abc import ABC

from gadgets.i_update_container import IUpdateContainer


class IRemoteGadgetUpdateContainer(IUpdateContainer, ABC):
    _client: bool

    def __init__(self):
        super().__init__()
        self._client = False

    @property
    def client(self) -> bool:
        return self._client

    def set_client(self):
        with self._get_lock():
            self._client = True
            self._record_change()
