import json
import logging
import sys
import threading
import time
from abc import ABCMeta
from typing import Optional, Callable

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from homekit.model.services import LightBulbService
from homekit.model.services import BHSLightBulbService
from homekit.model import get_id
from homekit.model.characteristics import OnCharacteristicMixin
from homekit.model.services import ServicesTypes, AbstractService

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.any_gadget import AnyGadget
from gadgets.gadget import Gadget
from lib.logging_interface import LoggingInterface
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher

MANUFACTURER = "j_klink"
SERIAL_NUMBER = "00001"
REVISION = "0.1.4"
HOMEKIT_SERVER_NAME = "HomekitAccessoryServer"


def light_switched(new_value):
    print('=======>  light status switched: {x}'.format(x=new_value))


def light_hue(new_value):
    print('=======>  light hue switched: {x}'.format(x=new_value))


def light_sat(new_value):
    print('=======>  light sat switched: {x}'.format(x=new_value))


def light_bri(new_value):
    print('=======>  light brightness switched: {x}'.format(x=new_value))


def switch_triggered(new_value):
    print(f"Switch -> {new_value}")


def status_cb():
    print("IDENTIFY")


class SwitchService(AbstractService, OnCharacteristicMixin):

    def __init__(self):
        AbstractService.__init__(self, ServicesTypes.get_uuid('public.hap.service.switch'), get_id())
        OnCharacteristicMixin.__init__(self, get_id())


class HomekitAccessoryWrapper(LoggingInterface, GadgetUpdatePublisher, metaclass=ABCMeta):
    _name: str
    _accessory: Accessory

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._accessory = Accessory(self._name,
                                    MANUFACTURER,
                                    self.__class__.__name__,
                                    SERIAL_NUMBER,
                                    REVISION)
        self._accessory.set_identify_callback(status_cb)

    @property
    def accessory(self) -> Accessory:
        return self._accessory


class HomekitRGBLamp(HomekitAccessoryWrapper):
    _status: int
    _hue: int
    _brightness: int
    _saturation: int

    def __init__(self, name: str):
        super().__init__(name)

        self._status = 1
        self._hue = 100
        self._brightness = 55
        self._saturation = 100

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

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, value: int):
        self._status = value

    def _callback_set_status(self) -> Callable:
        def func(new_value):
            print(f"Status Changed: {new_value}")
            self._status = new_value

        return func

    def _callback_set_hue(self) -> Callable:
        def func(new_value):
            print(f"Hue Changed: {new_value}")
            self._hue = new_value

        return func

    def _callback_set_brightness(self) -> Callable:
        def func(new_value):
            print(f"Brightness Changed: {new_value}")
            self._brightness = new_value

        return func

    def _callback_set_saturation(self) -> Callable:
        def func(new_value):
            print(f"Saturation Changed: {new_value}")
            self._saturation = new_value

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            print(f"Accessing status ({self._status})")
            return self._status

        return func

    def _callback_get_hue(self) -> Callable:
        def func():
            print(f"Accessing Hue ({self._hue})")
            return self._hue

        return func

    def _callback_get_brightness(self) -> Callable:
        def func():
            print(f"Accessing Brightness ({self._brightness})")
            return self._brightness

        return func

    def _callback_get_saturation(self) -> Callable:
        def func():
            print(f"Accessing Saturation ({self._saturation})")
            return self._saturation

        return func


class GadgetPublisherHomekit(GadgetPublisher):
    _config_file: str
    _homekit_server: AccessoryServer
    _server_thread: Optional[threading.Thread]

    def __init__(self, config: str):
        super().__init__()
        self._logger.info("Starting...")
        self._config_file = config
        server_logger = logging.getLogger(HOMEKIT_SERVER_NAME)
        self._homekit_server = AccessoryServer(self._config_file, server_logger)
        dummy_accessory = Accessory("PythonBridge", MANUFACTURER, "tester_version", "00001", "0.3")
        self._homekit_server.add_accessory(dummy_accessory)
        self._server_thread = None
        self.start_server()

        self.test_rgb_lamp = HomekitRGBLamp("dummy_rgb_lamp")
        self._homekit_server.add_accessory(self.test_rgb_lamp.accessory)
        self._homekit_server.set_identify_callback(status_cb)

    def __del__(self):
        super().__del__()
        self.stop_server()

    def stop_server(self):
        if self._server_thread is None:
            return
        self._logger.info("Stopping Accessory Server")
        self._homekit_server.shutdown()
        self._server_thread.join()
        self._server_thread = None

    def start_server(self):
        if self._server_thread is not None:
            self.stop_server()
        self._logger.info("Starting Accessory Server")
        self._homekit_server.publish_device()
        self._server_thread = threading.Thread(target=self._homekit_server.serve_forever,
                                               args=[3],
                                               name=HOMEKIT_SERVER_NAME,
                                               daemon=True)
        self._server_thread.start()

    def reset_config(self):
        with open(self._config_file, "r") as file_p:
            cfg_data = json.load(file_p)

        new_config = {
            x: cfg_data[x] for x in ["accessory_pairing_id", "c#", "category", "host_ip", "host_port", "name"]
        }

        with open(self._config_file, "w") as file_p:
            json.dump(new_config, file_p)

    def receive_gadget(self, gadget: Gadget):
        pass

    def create_gadget(self, gadget: Gadget):
        pass

    def remove_gadget(self, gadget_name: str) -> bool:
        pass

    def receive_gadget_update(self, gadget: Gadget):
        pass


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    config_file = "temp/demoserver.json"

    if int(sys.argv[1]) == 0:
        print("Object")
        server = GadgetPublisherHomekit(config_file)

        for i in range(30):
            time.sleep(5)
            print(".")
            new_status = 0 if server.test_rgb_lamp.status else 1
            server.test_rgb_lamp.status = new_status
            print(f"CHANGING STATUS TO {new_status}")
            # server._homekit_server.unpublish_device()
            # server._homekit_server.publish_device()

        server.__del__()
    else:
        print("Old")

        try:
            logger = logging.getLogger('accessory')
            httpd = AccessoryServer(config_file, logger)

            dummy_accessory = Accessory("PythonBridge", MANUFACTURER, "tester_version", "00001", "0.3")
            httpd.add_accessory(dummy_accessory)

            rgb_light = Accessory('Testlicht_RGB', MANUFACTURER, 'BHSLightBulbService', '0001', '0.1')
            rgb_light_service = BHSLightBulbService()
            rgb_light_service.set_on_set_callback(light_switched)
            rgb_light_service.set_hue_set_callback(light_hue)
            rgb_light_service.set_brightness_set_callback(light_bri)
            rgb_light_service.set_saturation_set_callback(light_sat)
            rgb_light.services.append(rgb_light_service)

            light = Accessory('Testlicht', MANUFACTURER, 'LightBulbService', '0002', '0.2')
            light_service = LightBulbService()
            light_service.set_on_set_callback(light_switched)
            light.services.append(light_service)

            switch = Accessory('TestSwitch', MANUFACTURER, 'SwitchService', '0003', '0.1')
            switch_service = SwitchService()
            switch_service.set_on_set_callback(switch_triggered)
            switch.services.append(switch_service)

            httpd.add_accessory(rgb_light)
            httpd.add_accessory(light)
            httpd.add_accessory(switch)

            httpd.publish_device()
            logger.info('published device and start serving')
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
