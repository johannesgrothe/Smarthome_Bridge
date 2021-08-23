from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.gadgets.any_gadget import AnyGadget
from logging_interface import LoggingInterface


class GadgetFactory(LoggingInterface):

    def __init__(self):
        super().__init__()

    def create_gadget(self,
                      gadget_type: GadgetIdentifier,
                      name: str,
                      host_client: str,
                      characteristics: list[Characteristic]) -> Gadget:
        if gadget_type == GadgetIdentifier.fan_westinghouse_ir:
            raise NotImplementedError()
        elif gadget_type == GadgetIdentifier.lamp_basic:
            raise NotImplementedError()
        else:
            self._logger.info("No valid GadgetIdentifier found, Creating 'AnyGadget'")
            return AnyGadget(name, host_client, characteristics)
