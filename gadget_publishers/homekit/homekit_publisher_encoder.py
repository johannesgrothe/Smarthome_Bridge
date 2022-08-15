from gadget_publishers.homekit.homekit_accessory_denon_receiver import HomekitDenonReceiver
from gadget_publishers.homekit.homekit_accessory_fan import HomekitFan
from gadget_publishers.homekit.homekit_accessory_rgb_lamp import HomekitRGBLamp
from gadget_publishers.homekit.homekit_accessory_wrapper import HomekitAccessoryWrapper
from gadgets.gadget import Gadget
from gadgets.remote.remote_fan import Fan
from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget


class HomekitEncodeError(Exception):
    pass


class HomekitPublisherFactory:

    @staticmethod
    def encode(gadget: Gadget) -> HomekitAccessoryWrapper:
        """
        Creates a homekit accessory wrapper for the passed gadget

        :param gadget: Gadget to encode
        :return: A homekit accessory wrapper for the gadget
        :raises HomekitEncodeError: If encoding fails for any reason
        """
        if isinstance(gadget, RemoteLampRGB):
            return HomekitRGBLamp(gadget)
        elif isinstance(gadget, DenonRemoteControlGadget):
            return HomekitDenonReceiver(gadget)
        elif isinstance(gadget, Fan):
            return HomekitFan(gadget)
        raise HomekitEncodeError(f"Cannot encode gadget of type {gadget.__class__.__name__}")
