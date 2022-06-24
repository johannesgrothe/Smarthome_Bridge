from gadgets.remote.lamp_rgb import LampRGB
from smarthome_bridge.api_decoders.api_decoder_super import ApiDecoderSuper
from smarthome_bridge.client_information_interface import ClientInformationInterface
from system.gadget_definitions import RemoteGadgetIdentifier, GadgetClass, GadgetClassMapping


class GadgetDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding gadget")


class RemoteGadgetDecoder(ApiDecoderSuper):
    @classmethod
    def decode(cls, gadget_data: dict, host: ClientInformationInterface) -> object:
        """
        Decodes a gadget out of the data given

        :param gadget_data: The json data to parse the gadget from
        :param host: Host-Client of the gadget
        :return: The parsed gadget
        :raises GadgetDecodeError: If anything goes wrong decoding the gadget
        """
        try:
            identifier = RemoteGadgetIdentifier(gadget_data["type"])
            gadget_class = None
            for g_class, types in GadgetClassMapping:
                if identifier in types:
                    gadget_class = g_class

            if gadget_class is None:
                raise GadgetDecodeError()

            if gadget_class == GadgetClass.lamp_rgb:
                return LampRGB(gadget_data["id"],
                               host,
                               gadget_data["red"],
                               gadget_data["green"],
                               gadget_data["blue"])
            else:
                raise GadgetDecodeError()

        except (KeyError, ValueError) as err:
            cls._get_logger().error(err.args[0])
            raise GadgetDecodeError()
