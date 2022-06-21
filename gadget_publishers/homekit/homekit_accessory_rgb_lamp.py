"""Module for the homekit rgb lamp"""
import colorsys
from typing import Callable

from homekit.model import BHSLightBulbService

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadgets.remote.lamp_rgb import LampRGB


class HomekitRGBLamp(HomekitAccessoryWrapper):
    """Class that realized a homekit rgb lamp"""

    _origin: LampRGB

    def __init__(self, origin: LampRGB):
        """
        Constructor for the homekit rgb lamp

        :param origin: Gadget represented by this wrapper class
        """
        super().__init__(origin)

        self._status = origin.rgb != (0, 0, 0)
        hue, saturation, value = colorsys.rgb_to_hsv(origin.red, origin.green, origin.blue)
        self._hue = hue
        self._brightness = value
        self._saturation = saturation

        rgb_light_service = BHSLightBulbService()

        rgb_light_service.set_on_set_callback(self._callback_set_status())
        rgb_light_service.set_hue_set_callback(self._callback_set_hue())
        rgb_light_service.set_brightness_set_callback(self._callback_set_brightness())
        rgb_light_service.set_saturation_set_callback(self._callback_set_saturation())

        rgb_light_service.set_on_get_callback(self._callback_get_status())
        rgb_light_service.set_hue_get_callback(self._callback_get_hue())
        rgb_light_service.set_brightness_get_callback(self._callback_get_brightness())
        rgb_light_service.set_saturation_get_callback(self._callback_get_saturation())

        self._accessory.add_service(rgb_light_service)

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            if not new_value:
                self._origin.rgb = (0, 0, 0)

        return func

    def _callback_set_hue(self) -> Callable:
        def func(new_value):
            h, s, v = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            rgb = colorsys.hsv_to_rgb(new_value, s, v)
            self._origin.rgb = rgb

        return func

    def _callback_set_brightness(self) -> Callable:
        def func(new_value):
            h, s, v = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            rgb = colorsys.hsv_to_rgb(h, s, new_value)
            self._origin.rgb = rgb

        return func

    def _callback_set_saturation(self) -> Callable:
        def func(new_value):
            h, s, v = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            rgb = colorsys.hsv_to_rgb(h, new_value, v)
            self._origin.rgb = rgb

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self._origin.rgb != (0, 0, 0)

        return func

    def _callback_get_hue(self) -> Callable:
        def func():
            hue, _, _ = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            return hue

        return func

    def _callback_get_brightness(self) -> Callable:
        def func():
            _, _, value = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            return value

        return func

    def _callback_get_saturation(self) -> Callable:
        def func():
            _, saturation, _ = colorsys.rgb_to_hsv(self._origin.red, self._origin.green, self._origin.blue)
            return saturation

        return func
