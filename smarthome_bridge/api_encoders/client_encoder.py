from lib.logging_interface import ILogging
from smarthome_bridge.api_encoders import DATETIME_FORMAT
from smarthome_bridge.api_encoders.gadget_api_encoder import GadgetEncodeError
from smarthome_bridge.client import Client


class ClientApiEncoder(ILogging):

    @classmethod
    def encode_all_clients_info(cls, client_info: list[Client]) -> dict:
        client_data = []
        for client in client_info:
            try:
                client_data.append(cls.encode_client(client))
            except GadgetEncodeError:
                cls._get_logger().error(f"Failed to encode client '{client.id}'")
        return {"clients": client_data}

    @classmethod
    def encode_client(cls, client: Client) -> dict:
        """
        Serializes a clients data according to api specification

        :param client: The client to serialize
        :return: The serialized version of the client as dict
        """
        cls._get_logger().debug(f"Serializing client '{client.id}'")

        software_info = None
        if client.software_info is not None:
            software_info = {
                "uploaded": client.software_info.date.strftime(DATETIME_FORMAT),
                "commit": client.software_info.commit,
                "branch": client.software_info.branch,
            }

        return {"id": client.id,
                "created": client.created.strftime(DATETIME_FORMAT),
                "last_connected": client.last_connected.strftime(DATETIME_FORMAT),
                "runtime_id": client.runtime_id,
                "is_active": client.is_active,
                "boot_mode": client.boot_mode,
                "software": software_info,
                "port_mapping": client.get_port_mapping(),
                "api_version": str(client.api_version)}
