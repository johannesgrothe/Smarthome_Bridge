from gadgets.remote_gadget import Gadget
from lib.logging_interface import LoggingInterface
from smarthome_bridge.characteristic import Characteristic


class LocalGadget(LoggingInterface):
    _name: str

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name
