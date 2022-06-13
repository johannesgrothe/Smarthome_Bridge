import logging
import os.path
import sys
import threading
import time
from typing import Optional

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from homekit.model.services import LightBulbService
from homekit.model.services import BHSLightBulbService
from gadget_publishers.gadget_publisher import GadgetPublisher, GadgetCreationError, GadgetDeletionError
from gadget_publishers.homekit.homekit_accessory_constants import HomekitConstants
from gadget_publishers.homekit.homekit_accessory_denon_receiver import HomekitDenonReceiver
from gadget_publishers.homekit.homekit_accessory_rgb_lamp import HomekitRGBLamp
from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_config_manager import HomekitConfigManager
from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadget_publishers.homekit.homekit_publisher_encoder import HomekitEncodeError, HomekitPublisherFactory
from gadget_publishers.homekit.homekit_services import SwitchService
from gadgets.gadget_update_container import GadgetUpdateContainer
from gadgets.remote.lamp_rgb import LampRGB, LampRgbUpdateContainer
from gadgets.remote.remote_gadget import Gadget
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget, DenonRemoteControlGadgetUpdateContainer
from lib.color_converter import ColorConverter

RESTART_DELAY = 7
HOMEKIT_SERVER_NAME = "HomekitAccessoryServer"


class GadgetDoesNotExistError(Exception):
    pass


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
        if not os.path.isfile(self._config_file):
            HomekitConfigManager(self._config_file).generate_new_config()

        self._gadgets = []
        self._server_logger = logging.getLogger(HOMEKIT_SERVER_NAME)
        self._server_thread = None
        self._restart_scheduled = False
        self._dummy_accessory = Accessory("PythonBridge",
                                          HomekitConstants().manufacturer,
                                          self.__class__.__name__,
                                          "1776",
                                          HomekitConstants().revision)

        self.start_server()

    def __del__(self):
        super().__del__()
        self._restart_scheduled = False
        self.stop_server()

    @property
    def config(self) -> HomekitConfigManager:
        return HomekitConfigManager(self._config_file)

    def receive_update_from_gadget(self, gadget: str, update_data: dict) -> None:
        if gadget == self._last_published_gadget:
            return
        if self._status_supplier is None:
            self._logger.info(f"Cannot publish Gadget Info")
            return

        origin_gadget = self._status_supplier.get_gadget(gadget)
        if origin_gadget is None:
            return
        if isinstance(origin_gadget, LampRGB):
            status = update_data["status"]
            hue = update_data["hue"]
            saturation = update_data["saturation"]
            brightness = update_data["brightness"]

            if not status:
                origin_gadget.rgb = (0, 0, 0)
            else:
                rgb = ColorConverter.hsv_to_rgb([hue, saturation, brightness])
                origin_gadget.rgb = (rgb[0], rgb[1], rgb[2])

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

    def _schedule_restart(self):

        def restart_method(seconds: int):
            self._logger.info(f"Restarting in {seconds}s")
            time.sleep(seconds)
            if self._restart_scheduled:
                self.start_server()

        restart_thread = threading.Thread(target=restart_method,
                                          args=[RESTART_DELAY],
                                          name=f"{self.__class__.__name__}RestartThread",
                                          daemon=True)
        self._restart_scheduled = True
        restart_thread.start()

    def _gadget_exists(self, name: str):
        return name in [x.name for x in self._gadgets]

    def _get_gadget(self, gadget_name: str) -> HomekitAccessoryWrapper:
        found = [x for x in self._gadgets if x.name == gadget_name]
        if not found:
            raise GadgetDoesNotExistError("Gadget does not exist")
        if len(found) != 1:
            raise Exception(f"More than one gadget with name {gadget_name} exists")
        return found[0]

    def create_gadget(self, gadget: Gadget):
        if self._gadget_exists(gadget.id):
            raise GadgetCreationError(gadget.id)
        try:
            gadget = HomekitPublisherFactory.encode(self, gadget)
            self._homekit_server.add_accessory(gadget.accessory)
            self._gadgets.append(gadget)
            self._homekit_server.publish_device()
            self._schedule_restart()
        except HomekitEncodeError:
            self._logger.info(f"Cannot create accessory for '{gadget.__class__.__name__}'")
            return

    def add_gadget(self, gadget_id: str):
        try:
            self.remove_gadget(gadget_id)
        except GadgetDeletionError:
            pass
        origin = self._status_supplier.get_gadget(gadget_id)
        self.create_gadget(origin)

    def remove_gadget(self, gadget_id: str):
        try:
            found = self._get_gadget(gadget_id)
            self._gadgets.remove(found)
            self._schedule_restart()
        except GadgetDoesNotExistError:
            raise GadgetDeletionError(gadget_id)

    def _receive_gadget_update_rgb_lamp(self, origin: Gadget, wrapper: HomekitAccessoryWrapper,
                                        container: LampRgbUpdateContainer):

        if not isinstance(wrapper, HomekitRGBLamp):
            self._logger.error(
                f"Incompatible types: {container.__class__.__name__} and {wrapper.__class__.__name__}")
            return
        if not isinstance(origin, LampRGB):
            self._logger.error(
                f"Incompatible types: {container.__class__.__name__} and {origin.__class__.__name__}")
            return
        if container.rgb:
            rgb = origin.rgb
            if rgb == (0, 0, 0):
                wrapper.status = 0
            else:
                wrapper.status = 1

                r, g, b = rgb
                hsv = ColorConverter.rgb_to_hsv([r, g, b])
                wrapper.hue = hsv[0]
                wrapper.saturation = hsv[1]
                wrapper._publisher = hsv[2]

    def _receive_gadget_update_receiver(self, origin: Gadget, wrapper: HomekitAccessoryWrapper,
                                        container: DenonRemoteControlGadgetUpdateContainer):

        if not isinstance(wrapper, HomekitDenonReceiver):
            self._logger.error(
                f"Incompatible types: {container.__class__.__name__} and {wrapper.__class__.__name__}")
            return
        if not isinstance(origin, DenonRemoteControlGadget):
            self._logger.error(
                f"Incompatible types: {container.__class__.__name__} and {origin.__class__.__name__}")
            return

        if container.status:
            wrapper.status = 1 if origin.status else 0

    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        try:
            origin = self._status_supplier.get_gadget(update_container.origin)
            wrapper = self._get_gadget(update_container.origin)

            if isinstance(update_container, LampRgbUpdateContainer):
                return self._receive_gadget_update_rgb_lamp(origin, wrapper, update_container)
            elif isinstance(update_container, DenonRemoteControlGadgetUpdateContainer):
                return self._receive_gadget_update_receiver(origin, wrapper, update_container)
            else:
                self._logger.error(f"Not Implemented: {update_container.__class__.__name__}")

        except GadgetDoesNotExistError:
            origin_gadget = self._status_supplier.get_gadget(gadget_id)
            self.create_gadget(origin_gadget)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    config_file = "temp/demoserver.json"

    if int(sys.argv[1]) == 0:
        print("Object Mode")
        server = GadgetPublisherHomekit(config_file)

        input("Press enter to continue")

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
        print("Function Mode")

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
