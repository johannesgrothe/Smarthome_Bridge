from typing import Callable

from homekit.model import BHSLightBulbService

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface


class HomekitRGBLamp(HomekitAccessoryWrapper):
    _status: int
    _hue: int
    _brightness: int
    _saturation: int

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface, status: int, hue: int, brightness: int,
                 saturation: int):
        super().__init__(name, publisher)

        self._status = status
        self._hue = hue
        self._brightness = brightness
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

    def _trigger_update(self):
        update_data = {
            "status": self.status,
            "hue": self.hue,
            "saturation": self.saturation,
            "brightness": self.brightness
        }
        self._publisher.receive_update(self.name, update_data)

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, value: int):
        if self._status != value:
            self._status = value
            self._trigger_update()

    @property
    def hue(self) -> int:
        return self._hue

    @hue.setter
    def hue(self, value: int):
        if self._hue != value:
            self._hue = value
            self._trigger_update()

    @property
    def saturation(self) -> int:
        return self._saturation

    @saturation.setter
    def saturation(self, value: int):
        if self._saturation != value:
            self._saturation = value
            self._trigger_update()

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int):
        if self._brightness != value:
            self._brightness = value
            self._trigger_update()

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            self.status = new_value

        return func

    def _callback_set_hue(self) -> Callable:
        def func(new_value):
            self.hue = new_value

        return func

    def _callback_set_brightness(self) -> Callable:
        def func(new_value):
            self.brightness = new_value

        return func

    def _callback_set_saturation(self) -> Callable:
        def func(new_value):
            self.saturation = new_value

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self.status

        return func

    def _callback_get_hue(self) -> Callable:
        def func():
            return self.hue

        return func

    def _callback_get_brightness(self) -> Callable:
        def func():
            return self.brightness

        return func

    def _callback_get_saturation(self) -> Callable:
        def func():
            return self.saturation

        return func
