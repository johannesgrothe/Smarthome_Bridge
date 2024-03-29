from gadget_publishers.gadget_publisher import GadgetPublisher
from lib.logging_interface import ILogging
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.local.i_local_gadget import ILocalGadget


class LocalGadgetManager(ILogging):
    _gadgets: list[ILocalGadget]
    _gadget_publishers: list[GadgetPublisher]

    def __init__(self):
        super().__init__()
        self._gadgets = []
        self._gadget_publishers = []

        self._gadgets.append(DenonRemoteControlGadget("DenonReceiver",
                                                      "192.168.178.155"))

    def __del__(self):
        pass

    @property
    def gadgets(self) -> list[ILocalGadget]:
        return self._gadgets
