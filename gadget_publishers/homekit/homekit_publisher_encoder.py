from gadget_publishers.homekit.homekit_accessory_denon_receiver import HomekitDenonReceiver
from gadget_publishers.homekit.homekit_accessory_rgb_lamp import HomekitRGBLamp
from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from gadgets.remote_gadget import Gadget
from local_gadgets.denon_remote_control_gadget import DenonRemoteControlGadget
from system.gadget_definitions import CharacteristicIdentifier


class HomekitEncodeError(Exception):
    pass


class HomekitPublisherFactory:

    @staticmethod
    def encode(publisher: GadgetPublisherHomekitInterface, gadget: Gadget) -> HomekitAccessoryWrapper:
        """
        Creates a homekit accessory wrapper for the passed gadget

        :param publisher: Publisher to attach to accessory wrapper
        :param gadget: Gadget to encode
        :return: A homekit accessory wrapper for the gadget
        :raises HomekitEncodeError: If encoding fails for any reason
        """
        if isinstance(gadget, LampNeopixelBasic):
            return HomekitRGBLamp(gadget.get_name(),
                                  publisher,
                                  gadget.get_characteristic(CharacteristicIdentifier.status).get_step_value(),
                                  gadget.get_characteristic(CharacteristicIdentifier.hue).get_step_value(),
                                  gadget.get_characteristic(
                                      CharacteristicIdentifier.brightness).get_step_value(),
                                  gadget.get_characteristic(
                                      CharacteristicIdentifier.saturation).get_step_value())
        elif isinstance(gadget, DenonRemoteControlGadget):
            return HomekitDenonReceiver(gadget.id,
                                        publisher,
                                        gadget.status)
        raise HomekitEncodeError(f"Cannot encode gadget of type {gadget.__class__.__name__}")
