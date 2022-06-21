"""Module for the homekit rgb lamp"""
from typing import Callable

from homekit.model import FanService

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadgets.remote.fan import Fan


class HomekitFan(HomekitAccessoryWrapper):
    """Class that realized a homekit rgb lamp"""
    _origin: Fan

    _last_speed: int

    def __init__(self, origin: Fan):
        """
        Constructor for the homekit rgb lamp

        :param origin: Publisher for this gadget
        """
        super().__init__(origin)

        self._last_speed = 0

        service = FanService()
        service.set_on_set_callback(self._callback_set_status())
        service.set_on_get_callback(self._callback_get_status())

        self._accessory.add_service(service)

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            if new_value == 0:
                self._last_speed = self._origin.speed
                self._origin.speed = 0
            else:
                self._origin.speed = self._last_speed

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self._origin.speed > 0

        return func
