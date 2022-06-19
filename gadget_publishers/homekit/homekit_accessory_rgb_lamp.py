"""Module for the homekit rgb lamp"""
from typing import Callable

from homekit.model import BHSLightBulbService

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadgets.remote.lamp_rgb import LampRGB
from lib.color_converter import ColorConverter


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
        hsv = ColorConverter.rgb_to_hsv([origin.red, origin.green, origin.blue])
        self._hue = hsv[0]
        self._brightness = hsv[1]
        self._saturation = hsv[2]

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
            print(new_value)
            if not new_value:
                self._origin.rgb = (0, 0, 0)

        return func

    def _callback_set_hue(self) -> Callable:
        def func(new_value):
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            rgb = ColorConverter.hsv_to_rgb([new_value, hsv[1], hsv[2]])
            self._origin.rgb = (rgb[0], rgb[1], rgb[2])

        return func

    def _callback_set_brightness(self) -> Callable:
        def func(new_value):
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            rgb = ColorConverter.hsv_to_rgb([hsv[0], hsv[1], new_value])
            self._origin.rgb = (rgb[0], rgb[1], rgb[2])

        return func

    def _callback_set_saturation(self) -> Callable:
        def func(new_value):
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            rgb = ColorConverter.hsv_to_rgb([hsv[0], new_value, hsv[2]])
            self._origin.rgb = (rgb[0], rgb[1], rgb[2])

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self._origin.rgb != (0, 0, 0)

        return func

    def _callback_get_hue(self) -> Callable:
        def func():
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            return hsv[0]

        return func

    def _callback_get_brightness(self) -> Callable:
        def func():
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            return hsv[1]

        return func

    def _callback_get_saturation(self) -> Callable:
        def func():
            hsv = ColorConverter.rgb_to_hsv([self._origin.red, self._origin.green, self._origin.blue])
            return hsv[2]

        return func
