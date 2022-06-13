from typing import Type, Tuple, List

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from lib.logging_interface import ILogging
from smarthome_bridge.api_coders.api_encoder_super import ApiEncoderSuper
from smarthome_bridge.api_coders.gadget_publishers.gadget_publisher_homekit_encoder import GadgetPublisherHomekitEncoder

_gadget_publisher_name_mapping: dict[Type[GadgetPublisher], str] = {
    GadgetPublisherHomekit: "homekit",

}

_gadget_publisher_type_mapping: List[Tuple[Type[GadgetPublisher], Type[ApiEncoderSuper]]] = [
    (GadgetPublisherHomekit, GadgetPublisherHomekitEncoder)
]


class GadgetPublisherEncodeError(Exception):
    def __init__(self, class_name: str):
        super().__init__(f"Cannot encode {class_name}")


class GadgetPublisherApiEncoder(ILogging):

    @classmethod
    def encode_gadget_publisher_list(cls, publishers: list[GadgetPublisher]) -> dict:
        buf_list = []
        for publisher in publishers:
            try:
                buf_list.append(cls.encode_gadget_publisher(publisher))
            except GadgetPublisherEncodeError as err:
                cls._get_logger().error(err.args[0])
        return {
            "gadget_publishers": buf_list
        }

    @classmethod
    def encode_gadget_publisher(cls, publisher: GadgetPublisher) -> dict:

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
