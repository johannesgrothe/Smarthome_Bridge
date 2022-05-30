from gadget_publishers.homekit.homekit_accessory_denon_receiver import HomekitDenonReceiver
from gadget_publishers.homekit.homekit_accessory_rgb_lamp import HomekitRGBLamp
from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface
from gadgets.remote.lamp_rgb import LampRGB
from gadgets.remote.remote_gadget import Gadget
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from lib.color_converter import ColorConverter


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
        if isinstance(gadget, LampRGB):
            hsv = ColorConverter.rgb_to_hsv([gadget.red, gadget.green, gadget.blue])
            return HomekitRGBLamp(gadget.id,
                                  publisher,
                                  0 if gadget.rgb == (0, 0, 0) else 1,
                                  hsv[0],
                                  hsv[1],
                                  hsv[2])
        elif isinstance(gadget, DenonRemoteControlGadget):
            return HomekitDenonReceiver(gadget.id,
                                        publisher,
                                        gadget.status)
        raise HomekitEncodeError(f"Cannot encode gadget of type {gadget.__class__.__name__}")
