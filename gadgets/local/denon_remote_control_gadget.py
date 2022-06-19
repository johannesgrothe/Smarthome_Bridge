import logging
import time
from typing import Union, List

from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.local.local_gadget import LocalGadget
import denonavr

from utils.thread_manager import ThreadManager


class SourceError(Exception):
    pass


class DenonRemoteControlGadgetUpdateContainer(GadgetUpdateContainer):
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
        with self._lock:
            self._status = True
            self._record_change()

    @property
    def source(self) -> bool:
        return self._source

    def set_source(self):
        with self._lock:
            self._source = True
            self._record_change()


class DenonRemoteControlGadget(LocalGadget):
    _status: bool
    _address: str
    _source: int
    _source_names: list[str]
    _update_container: DenonRemoteControlGadgetUpdateContainer
    _threads: ThreadManager

    def __init__(self, name: str, address: str):
        super().__init__(name)
        self._status = True
        self._source = 0
        self._address = address
        self._logger.info(f"Connecting to {self._address}")
        self._controller = denonavr.DenonAVR(self._address)

        self._controller.update()
        # if self._controller.power == "ON":
        #     self._status = True
        self._source_names = self._controller.input_func_list
        # self._source = self._get_source_index(self._controller.input_func)

        self._threads = ThreadManager()
        self._threads.add_thread(f"{self.__class__.__name__}UpdateThread", self._apply_updates)
        self._threads.start_threads()

    def _apply_updates(self):
        self._controller.update()
        power = self._controller.power
        if power is not None:
            self.status = True if power == "ON" else False

        source = self._controller.input_func
        if source is not None:
            self.source = source
        time.sleep(1)

    def reset_updated_properties(self):
        self._update_container = DenonRemoteControlGadgetUpdateContainer(self.id)

    def _get_source_index(self, name: str) -> int:
        for i, s_name in enumerate(self._source_names):
            if name == s_name:
                return i
        raise SourceError(f"Unknown Source: {name}")

    def _get_source_name(self, index: int) -> str:
        if index < 0:
            raise SourceError(f"Index is below 0: {index}")
        try:
            return self._source_names[index]
        except IndexError:
            raise SourceError(f"Source index too high: {index}")

    @property
    def status(self) -> bool:
        return self._status

    @status.setter
    def status(self, value: bool):
        if value != self._status:
            self._status = value
            self._logger.info(f"Setting power to {'ON' if value else 'OFF'}")
            if value:
                self._controller.power_on()
            else:
                self._controller.power_off()
            self._update_container.set_status()

    @property
    def source(self) -> int:
        return self._source

    @source.setter
    def source(self, value: Union[int, str]):
        if isinstance(value, str):
            value = self._get_source_index(value)
        if value != self._source:
            self._source = value
            source_name = self._get_source_name(value)
            self._logger.info(f"Setting source to {source_name}")
            self._controller.set_input_func(source_name)
            self._update_container.set_source()

    @property
    def source_names(self) -> List[str]:
        return self._source_names


def main():
    gadget = DenonRemoteControlGadget("denon_tester", "192.168.178.155")
    # gadget.status = False
    # time.sleep(10)
    # gadget.status = True
    #
    # time.sleep(10)
    # gadget.source = "PC"
    # time.sleep(10)
    # gadget.source = "Apple TV"
    # time.sleep(10)

    time.sleep(50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
