"""Module for the homekit rgb lamp"""
from typing import Callable

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_services import DenonReceiverService
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget


class HomekitDenonReceiver(HomekitAccessoryWrapper):
    """Class that realized a homekit rgb lamp"""
    _origin: DenonRemoteControlGadget

    def __init__(self, origin: DenonRemoteControlGadget):
        """
        Constructor for the homekit rgb lamp

        :param origin: Publisher for this gadget
        """
        super().__init__(origin)

        service = DenonReceiverService()
        service.set_on_set_callback(self._callback_set_status())
        service.set_on_get_callback(self._callback_get_status())

        self._accessory.add_service(service)

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            self._origin.status = new_value

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self._origin.status

        return func
