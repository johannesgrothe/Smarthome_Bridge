import logging
import time

from gadgets.local.local_gadget import LocalGadget
import denonavr


class SourceError(Exception):
    pass


class DenonRemoteControlGadget(LocalGadget):

    _status: bool
    _address: str
    _source: int
    _source_names: list[str]

    def __init__(self, name: str, address: str):
        super().__init__(name)
        self._status = True
        self._source = 0
        self._address = address
        self._logger.info(f"Connecting to {self._address}")
        self._controller = denonavr.DenonAVR(self._address)
        self._controller.update()

        if self._controller.power == "ON":
            self._status = True

        self._source_names = self._controller.input_func_list
        self._source = self._get_source_index(self._controller.input_func)

    def handle_attribute_update(self, attribute: str, value) -> None:
        pass

    def access_property(self, property_name: str):
        if property_name == "status":
            return self.status
        elif property_name == "source":
            return self.source
        return super().access_property(property_name)

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
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value != self._status:
            self._status = value
            self._logger.info(f"Setting power to {'ON' if value else 'OFF'}")
            if value:
                self._controller.power_on()
            else:
                self._controller.power_off()
            self._mark_attribute_for_update("status")

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if isinstance(value, str):
            value = self._get_source_index(value)
        if value != self._source:
            self._source = value
            source_name = self._get_source_name(value)
            self._logger.info(f"Setting source to {source_name}")
            self._controller.set_input_func(source_name)
        self._mark_attribute_for_update("source")

    @property
    def source_names(self):
        return self._source_names


def main():
    gadget = DenonRemoteControlGadget("denon_tester", "192.168.178.155")
    gadget.status = False
    time.sleep(10)
    gadget.status = True

    time.sleep(10)
    gadget.source = "PC"
    time.sleep(10)
    gadget.source = "Apple TV"
    time.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
