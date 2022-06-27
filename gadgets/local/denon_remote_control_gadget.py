import datetime
import logging
import threading
import time

from gadgets.classes.tv import TV, TvUpdateContainer
from gadgets.local.i_local_gadget import ILocalGadget
import denonavr
from denonavr.exceptions import AvrTimoutError

from gadgets.local.i_local_gadget_update_container import ILocalGadgetUpdateContainer
from utils.thread_manager import ThreadManager


class DenonRemoteControlGadgetUpdateContainer(TvUpdateContainer, ILocalGadgetUpdateContainer):
    def __init__(self, origin: str):
        TvUpdateContainer.__init__(self, origin)
        ILocalGadgetUpdateContainer.__init__(self)


class DenonRemoteControlGadget(TV, ILocalGadget):
    _status: bool
    _address: str
    _source: int
    _source_names: list[str]
    _update_lock: threading.Lock
    _update_container: DenonRemoteControlGadgetUpdateContainer
    _threads: ThreadManager
    _last_write: datetime.datetime

    def __init__(self, name: str, address: str):
        ILocalGadget.__init__(self)
        TV.__init__(self, name)

        self._status = True
        self._source = 0
        self._address = address
        self._logger.info(f"Connecting to {self._address}")
        self._controller = denonavr.DenonAVR(self._address)
        self._update_lock = threading.Lock()
        self._last_write = datetime.datetime(1900, 1, 1)

        self._controller.update()
        self._source_names = self._controller.input_func_list

        self._threads = ThreadManager()
        self._threads.add_thread(f"{self.__class__.__name__}UpdateThread", self._apply_updates)
        self._threads.start_threads()

    def __del__(self):
        self._threads.__del__()

    def _apply_updates(self):
        try:
            with self._update_lock:
                if (datetime.datetime.now() - self._last_write) < datetime.timedelta(seconds=3):
                    return
                self._controller.update()
            power = self._controller.power
            if power is not None:
                self.status = True if power == "ON" else False

            source = self._controller.input_func
            if source is not None:
                self.source = source
        except AvrTimoutError:
            pass
        time.sleep(1)

    def reset_updated_properties(self):
        self._update_container = DenonRemoteControlGadgetUpdateContainer(self.id)

    def _get_status(self) -> bool:
        return self._status

    def _set_status(self, value: bool) -> None:
        with self._update_lock:
            self._status = value
            if value:
                self._controller.power_on()
            else:
                self._controller.power_off()
            self._last_write = datetime.datetime.now()

    def _get_source(self) -> int:
        return self._source

    def _set_source(self, value: int) -> None:
        with self._update_lock:
            self._source = value
            source_name = self._get_source_name(value)
            self._controller.set_input_func(source_name)
            self._last_write = datetime.datetime.now()

    def _get_sources(self) -> list[str]:
        return self._source_names


def main():
    gadget = DenonRemoteControlGadget("denon_tester", "192.168.178.155")

    print(gadget.updated_properties.is_empty)
    gadget.reset_updated_properties()
    print(gadget.updated_properties.is_empty)

    print("Turn OFF")
    gadget.status = False
    time.sleep(10.1)

    print("Turn ON")
    gadget.status = True
    # time.sleep(10.1)

    # print("Src PC")
    # gadget.source = "PC"
    # time.sleep(10.1)
    #
    # print("Src TV")
    # gadget.source = "Apple TV"
    # # time.sleep(10.1)

    print(gadget.updated_properties.is_empty)

    print("Sleep 50")
    # time.sleep(50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
