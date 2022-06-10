from typing import Type, Tuple, List, Callable

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from smarthome_bridge.api_coders.api_encoder_super import ApiEncoderSuper
from smarthome_bridge.api_encoder import GadgetPublisherEncodeError

_gadget_publisher_name_mapping: dict[Type[GadgetPublisher], str] = {
    GadgetPublisherHomekit: "homekit"
}


class GadgetPublisherApiEncoder(ApiEncoderSuper):

    @classmethod
    def encode(cls, publisher: GadgetPublisher) -> dict:

        _gadget_publisher_type_mapping: List[Tuple[Type[GadgetPublisher], Callable]] = [
            (GadgetPublisherHomekit, cls._encode_gadget_publisher_homekit)
        ]

        try:
            out_data = {
                "type": _gadget_publisher_name_mapping[publisher.__class__]
            }
        except KeyError:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)

        detected = False
        for publisher_type, function in _gadget_publisher_type_mapping:
            if isinstance(publisher, publisher_type):
                out_data |= function(publisher)
                detected = True
        if not detected:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)

        return out_data

    @staticmethod
    def _encode_gadget_publisher_homekit(publisher: GadgetPublisherHomekit) -> dict:
        config_data = publisher.config.data
        if config_data is not None:
            return {
                "pairing_pin": config_data["accessory_pin"],
                "port": config_data["host_port"],
                "name": config_data["name"]
            }
        return {}
