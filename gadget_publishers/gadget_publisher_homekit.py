import json
import logging
import sys
import threading
import time
from abc import ABCMeta, abstractmethod
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
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from lib.logging_interface import LoggingInterface
from smarthome_bridge.characteristic import Characteristic
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher
from system.gadget_definitions import CharacteristicIdentifier

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


class GadgetPublisherHomekitInterface(metaclass=ABCMeta):

    @abstractmethod
    def receive_update(self, gadget_name: str, update_data: dict):
        pass


class SwitchService(AbstractService, OnCharacteristicMixin):

    def __init__(self):
        AbstractService.__init__(self, ServicesTypes.get_uuid('public.hap.service.switch'), get_id())
        OnCharacteristicMixin.__init__(self, get_id())


class HomekitAccessoryWrapper(LoggingInterface, GadgetUpdatePublisher, metaclass=ABCMeta):
    _name: str
    _accessory: Accessory
    _publisher: GadgetPublisherHomekitInterface

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface):
        super().__init__()
        self._name = name
        self._publisher = publisher
        self._accessory = Accessory(self._name,
                                    MANUFACTURER,
                                    self.__class__.__name__,
                                    SERIAL_NUMBER,
                                    REVISION)
        self._accessory.set_identify_callback(status_cb)

    @property
    def name(self) -> str:
        return self._name

    @property
    def accessory(self) -> Accessory:
        return self._accessory


class HomekitRGBLamp(HomekitAccessoryWrapper):
    _status: int
    _hue: int
    _brightness: int
    _saturation: int

    def __init__(self, name: str, publisher: GadgetPublisherHomekitInterface, status: int, hue: int, brightness: int,
                 saturation: int):
        super().__init__(name, publisher)

        print("creating rgblamp")

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
            print(f"Status Changed: {new_value}")
            self.status = new_value

        return func

    def _callback_set_hue(self) -> Callable:
        def func(new_value):
            print(f"Hue Changed: {new_value}")
            self.hue = new_value

        return func

    def _callback_set_brightness(self) -> Callable:
        def func(new_value):
            print(f"Brightness Changed: {new_value}")
            self.brightness = new_value

        return func

    def _callback_set_saturation(self) -> Callable:
        def func(new_value):
            print(f"Saturation Changed: {new_value}")
            self.saturation = new_value

        return func

    def _callback_get_status(self) -> Callable:
        def func():
            print(f"Accessing status ({self._status})")
            return self.status

        return func

    def _callback_get_hue(self) -> Callable:
        def func():
            print(f"Accessing Hue ({self._hue})")
            return self.hue

        return func

    def _callback_get_brightness(self) -> Callable:
        def func():
            print(f"Accessing Brightness ({self._brightness})")
            return self.brightness

        return func

    def _callback_get_saturation(self) -> Callable:
        def func():
            print(f"Accessing Saturation ({self._saturation})")
            return self.saturation

        return func


class GadgetPublisherHomekit(GadgetPublisher, GadgetPublisherHomekitInterface):
    _config_file: str
    _server_logger: logging.Logger
    _homekit_server: AccessoryServer
    _server_thread: Optional[threading.Thread]
    _gadgets: list[HomekitAccessoryWrapper]
    _restart_scheduled: bool

    def __init__(self, config: str):
        super().__init__()
        self._logger.info("Starting...")
        self._config_file = config
        self._gadgets = []
        self._server_logger = logging.getLogger(HOMEKIT_SERVER_NAME)
        self._server_thread = None
        self._restart_scheduled = False
        self._dummy_accessory = Accessory("PythonBridge", MANUFACTURER, "tester_version", "00001", "0.3")

        self.start_server()

    def __del__(self):
        super().__del__()
        self._restart_scheduled = False
        self.stop_server()

    def receive_update(self, gadget: str, update_data: dict):
        if gadget == self._last_published_gadget:
            print("pass")
        if self._status_supplier is None:
            self._logger.info(f"Cannot publish Gadget Info")
            return

        origin_gadget = self._status_supplier.get_gadget(gadget)
        if origin_gadget is None:
            return
        characteristics = None
        if isinstance(origin_gadget, LampNeopixelBasic):
            characteristics = []
            for c_name, c_id in [
                ("status", CharacteristicIdentifier.status),
                ("hue", CharacteristicIdentifier.hue),
                ("saturation", CharacteristicIdentifier.saturation),
                ("brightness", CharacteristicIdentifier.brightness)
            ]:
                characteristics.append(Characteristic(c_id,
                                                      0,
                                                      1000,
                                                      value=update_data[c_name]))
        if characteristics is None:
            return
        out_gadget = AnyGadget(gadget,
                               "",
                               characteristics)

        self._publish_gadget(out_gadget)

    def _gen_server_method(self) -> Callable:
        def func():
            self._homekit_server.serve_forever(3)

        return func

    def stop_server(self):
        if self._server_thread is None:
            self._logger.info("Accessory Server is not running")
            return
        self._logger.info("Stopping Accessory Server")
        self._homekit_server.unpublish_device()
        self._homekit_server.shutdown()
        self._server_thread.join()
        self._server_thread = None

    def start_server(self):
        if self._server_thread is not None:
            self.stop_server()
        self._logger.info("Starting Accessory Server")
        self._homekit_server = AccessoryServer(self._config_file, self._server_logger)

        self._homekit_server.add_accessory(self._dummy_accessory)

        for gadget in self._gadgets:
            self._homekit_server.add_accessory(gadget.accessory)
        self._homekit_server.publish_device()
        self._server_thread = threading.Thread(target=self._homekit_server.serve_forever,
                                               args=[0.5],
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

    def _schedule_restart(self):

        def restart_method(seconds: int):
            self._logger.info(f"Restarting in {seconds}s")
            time.sleep(seconds)
            if self._restart_scheduled:
                self.start_server()

        restart_thread = threading.Thread(target=restart_method,
                                          args=[5],
                                          name=f"{self.__class__.__name__}RestartThread",
                                          daemon=True)
        self._restart_scheduled = True
        restart_thread.start()

    def _gadget_exists(self, name: str):
        return name in [x.name for x in self._gadgets]

    def _get_gadget(self, gadget_name: str) -> HomekitAccessoryWrapper:
        found = [x for x in self._gadgets if x.name == gadget_name]
        if not found:
            raise Exception("Gadget does not exist")
        if len(found) != 1:
            raise Exception(f"More than one gadget with name {gadget_name} exists")
        return found[0]

    def receive_gadget(self, gadget: Gadget):
        if self._gadget_exists(gadget.get_name()):
            # self.remove_gadget(gadget.get_name())
            homekit_gadget = self._get_gadget(gadget.get_name())
            if isinstance(homekit_gadget, HomekitRGBLamp):
                print("should sync")
                homekit_gadget.status = gadget.get_characteristic(CharacteristicIdentifier.status).get_step_value()
                homekit_gadget.hue = gadget.get_characteristic(CharacteristicIdentifier.hue).get_step_value()
                homekit_gadget.saturation = gadget.get_characteristic(
                    CharacteristicIdentifier.saturation).get_step_value()
                homekit_gadget.brightness = gadget.get_characteristic(
                    CharacteristicIdentifier.brightness).get_step_value()
            return
        self.create_gadget(gadget)

    def create_gadget(self, gadget: Gadget):
        print(gadget.get_name())
        if self._gadget_exists(gadget.get_name()):
            raise Exception("gadget exists already")
        if isinstance(gadget, LampNeopixelBasic):
            self._logger.info(f"Creating gadget '{gadget.get_name()}'")
            homekit_gadget = HomekitRGBLamp(gadget.get_name(),
                                            self,
                                            gadget.get_characteristic(CharacteristicIdentifier.status).get_step_value(),
                                            gadget.get_characteristic(CharacteristicIdentifier.hue).get_step_value(),
                                            gadget.get_characteristic(
                                                CharacteristicIdentifier.brightness).get_step_value(),
                                            gadget.get_characteristic(
                                                CharacteristicIdentifier.saturation).get_step_value())
            self._homekit_server.add_accessory(homekit_gadget.accessory)
            self._gadgets.append(homekit_gadget)
            self._homekit_server.publish_device()
            self._schedule_restart()
        else:
            print("error")
            return

    def remove_gadget(self, gadget_name: str):
        found = self._get_gadget(gadget_name)
        self._gadgets.remove(found)

    def receive_gadget_update(self, gadget: Gadget):
        homekit_gadget = self._get_gadget(gadget.get_name())
        if isinstance(homekit_gadget, HomekitRGBLamp):
            status = gadget.get_characteristic(CharacteristicIdentifier.status)
            hue = gadget.get_characteristic(CharacteristicIdentifier.hue)
            brightness = gadget.get_characteristic(CharacteristicIdentifier.brightness)
            saturation = gadget.get_characteristic(CharacteristicIdentifier.saturation)

            if status is not None:
                homekit_gadget.status = status.get_step_value()

            if hue is not None:
                homekit_gadget.hue = hue.get_step_value()

            if brightness is not None:
                homekit_gadget.brightness = brightness.get_step_value()

            if saturation is not None:
                homekit_gadget.saturation = saturation.get_step_value()


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    config_file = "temp/demoserver.json"

    if int(sys.argv[1]) == 0:
        print("Object")
        server = GadgetPublisherHomekit(config_file)

        input("press enter to continue")

        server.receive_gadget(LampNeopixelBasic("yolo_lamp",
                                                "tester",
                                                Characteristic(
                                                    CharacteristicIdentifier.status,
                                                    0,
                                                    1,
                                                    value=1
                                                ),
                                                Characteristic(
                                                    CharacteristicIdentifier.hue,
                                                    0,
                                                    360,
                                                    value=25
                                                ),
                                                Characteristic(
                                                    CharacteristicIdentifier.saturation,
                                                    0,
                                                    100,
                                                    value=99
                                                ),
                                                Characteristic(
                                                    CharacteristicIdentifier.brightness,
                                                    0,
                                                    100,
                                                    value=88
                                                )))

        for i in range(30):
            time.sleep(5)
            print(".")

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
