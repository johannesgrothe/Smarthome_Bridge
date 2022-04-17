import logging

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from homekit.model.services import LightBulbService
from homekit.model.services import BHSLightBulbService
from homekit.model import get_id
from homekit.model.characteristics import OnCharacteristicMixin
from homekit.model.services import ServicesTypes, AbstractService


PRODUCER = "j_klink"


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('accessory')

    config_file = "temp/demoserver.json"

    try:
        httpd = AccessoryServer(config_file, logger)

        dummy_accessory = Accessory("PythonBridge", PRODUCER, "tester_version", "00001", "0.3")
        httpd.add_accessory(dummy_accessory)

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

        httpd.add_accessory(rgb_light)
        httpd.add_accessory(light)
        httpd.add_accessory(switch)

        httpd.publish_device()
        logger.info('published device and start serving')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
