import logging

from smarthome_bridge.gadgets.gadget import Gadget, GadgetIdentifier
from smarthome_bridge.characteristic import Characteristic

from smarthome_bridge.gadgets.any_gadget import AnyGadget


class GadgetFactory:

    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

    def create_gadget(self,
                      gadget_type: GadgetIdentifier,
                      name: str,
                      host_client: str,
                      characteristics: list[Characteristic]) -> Gadget:
        if gadget_type == GadgetIdentifier.fan_westinghouse_ir:
            pass
        elif gadget_type == GadgetIdentifier.lamp_basic:
            pass
        else:
            self._logger.info("No valid GadgetIdentifier found, Creating 'AnyGadget'")
            return AnyGadget(name, host_client, characteristics)
