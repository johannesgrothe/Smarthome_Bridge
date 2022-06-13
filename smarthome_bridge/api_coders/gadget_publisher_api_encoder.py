from typing import Type, Tuple, List

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from smarthome_bridge.api_coders.api_encoder_super import ApiEncoderSuper
from smarthome_bridge.api_coders.gadget_publishers.gadget_publisher_homekit_encoder import GadgetPublisherHomekitEncoder
from smarthome_bridge.api_encoder import GadgetPublisherEncodeError

_gadget_publisher_name_mapping: dict[Type[GadgetPublisher], str] = {
    GadgetPublisherHomekit: "homekit"
}

_gadget_publisher_type_mapping: List[Tuple[Type[GadgetPublisher], Type[ApiEncoderSuper]]] = [
    (GadgetPublisherHomekit, GadgetPublisherHomekitEncoder)
]


class GadgetPublisherApiEncoder(ApiEncoderSuper):

    @classmethod
    def encode(cls, publisher: GadgetPublisher) -> dict:

        try:
            out_data = {
                "type": _gadget_publisher_name_mapping[publisher.__class__]
            }
        except KeyError:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)

        detected = False
        for publisher_type, encoder_type in _gadget_publisher_type_mapping:
            if isinstance(publisher, publisher_type):
                out_data |= encoder_type.encode(publisher)
                detected = True
        if not detected:
            raise GadgetPublisherEncodeError(publisher.__class__.__name__)

        return out_data
