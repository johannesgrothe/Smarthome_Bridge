import logging

from homekit.accessoryserver import AccessoryServer
from homekit.model import Accessory
from homekit.model.services import LightBulbService
from homekit.model.services import BHSLightBulbService
from homekit.model.services import AccessoryInformationService


def light_switched(new_value):
    print('=======>  light switched: {x}'.format(x=new_value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('accessory')

    config_file = "temp/demoserver.json"

    try:
        httpd = AccessoryServer(config_file, logger)

        dummy_accessory = Accessory("PythonBridge", "j_klink", "tester_version", "00001", "0.3")
        httpd.add_accessory(dummy_accessory)

        accessory = Accessory('Testlicht', 'lusiardi.de', 'Demoserver', '0001', '0.1')
        # lightBulbService = LightBulbService()
        lightBulbService = BHSLightBulbService()
        lightBulbService.set_on_set_callback(light_switched)
        lightBulbService.set_hue_set_callback(light_switched)
        lightBulbService.set_brightness_set_callback(light_switched)
        lightBulbService.set_saturation_set_callback(light_switched)
        accessory.services.append(lightBulbService)

        accessory2 = Accessory('Testlicht2', 'LordAinz', 'Blubidiblub', '0002', '0.2')
        lightBulbService2 = LightBulbService()
        lightBulbService2.set_on_set_callback(light_switched)
        accessory2.services.append(lightBulbService2)

        # httpd.add_accessory(accessory)
        # httpd.add_accessory(accessory2)

        httpd.publish_device()
        logger.info('published device and start serving')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
