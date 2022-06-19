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
            return HomekitRGBLamp(gadget)
        elif isinstance(gadget, DenonRemoteControlGadget):
            return HomekitDenonReceiver(gadget)
        raise HomekitEncodeError(f"Cannot encode gadget of type {gadget.__class__.__name__}")
