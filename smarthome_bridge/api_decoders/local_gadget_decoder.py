from gadgets.gadget import Gadget
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from smarthome_bridge.api_decoders.api_decoder_super import ApiDecoderSuper
from smarthome_bridge.api_decoders.remote_gadget_decoder import GadgetDecodeError
from system.gadget_definitions import LocalGadgetIdentifier


class LocalGadgetDecoder(ApiDecoderSuper):
    @classmethod
    def decode(cls, gadget_data: dict) -> Gadget:
        """
        Decodes a gadget out of the data given

        :param gadget_data: The json data to parse the gadget from
        :return: The parsed gadget
        :raises GadgetDecodeError: If anything goes wrong decoding the gadget
        """
        try:
            identifier = LocalGadgetIdentifier(gadget_data["type"])
            gadget_id = gadget_data["id"]
            options = gadget_data["options"]

            if identifier == LocalGadgetIdentifier.denon_av_receiver:
                return DenonRemoteControlGadget(gadget_id,
                                                options["ip"])
            else:
                raise NotImplementedError()

        except (KeyError, ValueError) as err:
            cls._get_logger().error(err.args[0])
            raise GadgetDecodeError()
