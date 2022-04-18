import json
import logging
import threading
import time
from abc import ABCMeta
from typing import Optional

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from homekit.model.services import LightBulbService
from homekit.model.services import BHSLightBulbService
from homekit.model import get_id
from homekit.model.characteristics import OnCharacteristicMixin
from homekit.model.services import ServicesTypes, AbstractService

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.gadget import Gadget
from lib.logging_interface import LoggingInterface
from smarthome_bridge.gadget_pubsub import GadgetUpdatePublisher, GadgetUpdateSubscriber

PRODUCER = "j_klink"
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


class SwitchService(AbstractService, OnCharacteristicMixin):

    def __init__(self):
        AbstractService.__init__(self, ServicesTypes.get_uuid('public.hap.service.switch'), get_id())
        OnCharacteristicMixin.__init__(self, get_id())


class HomekitAccessoryWrapper(LoggingInterface):
    def __init__(self):
        super().__init__()


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
        dummy_accessory = Accessory("PythonBridge", PRODUCER, "tester_version", "00001", "0.3")
        self._homekit_server.add_accessory(dummy_accessory)
        self._server_thread = None
        self.start_server()

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
        self._homekit_server.serve_forever()
        self._server_thread = threading.Thread(target=self._homekit_server.serve_forever(3),
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

    rgb_light = Accessory('Testlicht_RGB', PRODUCER, 'BHSLightBulbService', '0001', '0.1')
    rgb_light_service = BHSLightBulbService()
    rgb_light_service.set_on_set_callback(light_switched)
    rgb_light_service.set_hue_set_callback(light_hue)
    rgb_light_service.set_brightness_set_callback(light_bri)
    rgb_light_service.set_saturation_set_callback(light_sat)
    rgb_light.services.append(rgb_light_service)

    light = Accessory('Testlicht', PRODUCER, 'LightBulbService', '0002', '0.2')
    light_service = LightBulbService()
    light_service.set_on_set_callback(light_switched)
    light.services.append(light_service)

    switch = Accessory('TestSwitch', PRODUCER, 'SwitchService', '0003', '0.1')
    switch_service = SwitchService()
    switch_service.set_on_set_callback(switch_triggered)
    switch.services.append(switch_service)

    config_file = "temp/demoserver.json"

    server = GadgetPublisherHomekit(config_file)
    # server._homekit_server.add_accessory(rgb_light)

    time.sleep(2)
    print(".")
    time.sleep(2)
    print(".")
    time.sleep(2)
    print(".")
    time.sleep(2)
    print(".")
    time.sleep(2)
    print(".")

    server.__del__()


if __name__ == "__main__":
    main()
