from lib.logging_interface import ILogging
from smarthome_bridge.api_coders import DATETIME_FORMAT
from smarthome_bridge.api_coders.gadget_api_encoder import GadgetEncodeError
from smarthome_bridge.client import Client


class ClientApiEncoder(ILogging):

    @classmethod
    def encode_all_clients_info(cls, client_info: list[Client]) -> dict:
        client_data = []
        for client in client_info:
            try:
                client_data.append(cls.encode_client(client))
            except GadgetEncodeError:
                cls._get_logger().error(f"Failed to encode client '{client.get_name()}'")
        return {"clients": client_data}

    @classmethod
    def encode_client(cls, client: Client) -> dict:
        """
        Serializes a clients data according to api specification

        :param client: The client to serialize
        :return: The serialized version of the client as dict
        """
        cls._get_logger().debug(f"Serializing client '{client.get_name()}'")
        out_date = None
        if client.get_sw_flash_time() is not None:
            out_date = client.get_sw_flash_time().strftime(DATETIME_FORMAT)

        return {"name": client.get_name(),
                "created": client.get_created().strftime(DATETIME_FORMAT),
                "last_connected": client.get_last_connected().strftime(DATETIME_FORMAT),
                "runtime_id": client.get_runtime_id(),
                "is_active": client.is_active(),
                "boot_mode": client.get_boot_mode(),
                "sw_uploaded": out_date,
                "sw_commit": client.get_sw_commit(),
                "sw_branch": client.get_sw_branch(),
                "port_mapping": client.get_port_mapping(),
                "api_version": str(client.get_api_version())}
