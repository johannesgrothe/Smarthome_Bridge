"""Module for the homekit rgb lamp"""
from typing import Callable

from homekit.model import BHSLightBulbService

from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface


class HomekitDenonReceiver(HomekitAccessoryWrapper):
    """Class that realized a homekit rgb lamp"""
    _status: int

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface, status: int):
        """
        Constructor for the homekit rgb lamp

        :param name: Name of the accessory
        :param publisher: Publisher for this gadget
        :param status: Initial value for the status
        """
        super().__init__(name, publisher)

        self._status = status

        rgb_light_service = BHSLightBulbService()
        rgb_light_service.set_on_set_callback(self._callback_set_status())
        rgb_light_service.set_on_get_callback(self._callback_get_status())

        self._accessory.add_service(rgb_light_service)

    def _trigger_update(self) -> None:
        """
        Updates the publisher with the characteristics

        :return: None
        """
        update_data = {
            "status": self.status
        }
        self._publisher.receive_update_from_gadget(self.name, update_data)

    @property
    def status(self) -> int:
        """Value of the status characteristic"""
        return self._status

    @status.setter
    def status(self, value: int):
        """Sets the status characteristic"""
        if self._status != value:
            self._status = value
            self._trigger_update()

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            self.status = new_value

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            return self.status

        return func
