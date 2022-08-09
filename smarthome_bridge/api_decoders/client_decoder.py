from datetime import datetime
from smarthome_bridge.api_decoders.api_decoder_super import ApiDecoderSuper
from smarthome_bridge.api_encoders import DATETIME_FORMAT
from smarthome_bridge.client import Client, ClientSoftwareInformationContainer
from system.utils.software_version import SoftwareVersion


class ClientDecodeError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Error decoding client: {message}")


class ClientDecoder(ApiDecoderSuper):
    @classmethod
    def decode(cls, client_data: dict, client_id: str) -> Client:
        """
        Parses a smarthome-client from the given data

        :param client_data: Data to parse the client from
        :param client_id: Id of the client to decode
        :return: The parsed client
        :raises ClientDecodeError: If anything goes wrong parsing the client
        """
        try:
            # client_name = client_data["id"]
            runtime_id = client_data["runtime_id"]
            port_mapping = client_data["port_mapping"]
            boot_mode = client_data["boot_mode"]
            api_version = SoftwareVersion.from_string(client_data["api_version"])

            software = None
            if client_data["software"] is not None:
                software = ClientSoftwareInformationContainer(
                    client_data["software"]["commit"],
                    client_data["software"]["branch"],
                    datetime.strptime(client_data["software"]["uploaded"], DATETIME_FORMAT)
                )

            out_client = Client(client_id,
                                runtime_id,
                                software,
                                port_mapping,
                                boot_mode,
                                api_version)
            return out_client
        except KeyError as err:
            raise ClientDecodeError(f"Key Error at '{err.args[0]}'")
