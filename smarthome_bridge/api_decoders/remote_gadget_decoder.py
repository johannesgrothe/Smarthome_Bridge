from gadgets.gadget import Gadget
from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from smarthome_bridge.api_decoders.api_decoder_super import ApiDecoderSuper
from smarthome_bridge.client_information_interface import ClientInformationInterface
from system.gadget_definitions import RemoteGadgetIdentifier, GadgetClass, GadgetClassMapping


class GadgetDecodeError(Exception):
    def __init__(self):
        super().__init__("Error decoding gadget")


class RemoteGadgetDecoder(ApiDecoderSuper):
    @classmethod
    def decode(cls, gadget_data: dict, host: ClientInformationInterface) -> Gadget:
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
            for g_class, types in GadgetClassMapping.items():
                remote_types = [x for x in types if isinstance(x, RemoteGadgetIdentifier)]
                if identifier in remote_types:
                    gadget_class = g_class
                    break

            if gadget_class is None:
                raise NotImplementedError()

            if gadget_class == GadgetClass.lamp_rgb:
                return RemoteLampRGB(gadget_data["id"],
                                     host,
                                     gadget_data["attributes"]["red"],
                                     gadget_data["attributes"]["green"],
                                     gadget_data["attributes"]["blue"])
            else:
                raise GadgetDecodeError()

        except (KeyError, ValueError) as err:
            cls._get_logger().error(err.args[0])
            raise GadgetDecodeError()
