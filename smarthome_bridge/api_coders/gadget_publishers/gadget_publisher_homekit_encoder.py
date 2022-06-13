from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from smarthome_bridge.api_coders.api_encoder_super import ApiEncoderSuper


class GadgetPublisherHomekitEncoder(ApiEncoderSuper):
    @classmethod
    def encode(cls, publisher: GadgetPublisherHomekit) -> dict:
        config_data = publisher.config.data
        if config_data is not None:
            return {
                "pairing_pin": config_data["accessory_pin"],
                "port": config_data["host_port"],
                "name": config_data["name"]
            }
        return {}
