import logging
from smarthome_bridge.smarthomeclient import SmarthomeClient


class Serializer:
    """Class to assist the api with serializing objects"""

    _logger: logging.Logger

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def serialize_client(self, client: SmarthomeClient) -> dict:
        """
        Serializes a clients data according to api specification

        :param client: The client to serialize
        :return: The serialized version of the client as dict
        """
        self._logger.debug(f"Serializing client '{client.get_name()}'")
        out_date = None
        if client.get_flash_date() is not None:
            out_date = client.get_flash_date().strftime("%Y-%m-%d %H:%M:%S")

        return {"name": client.get_name(),
                "created": client.get_created().strftime("%Y-%m-%d %H:%M:%S"),
                "last_connected": client.get_last_connected().strftime("%Y-%m-%d %H:%M:%S"),
                "is_active": client.is_active(),
                "boot_mode": client.get_boot_mode(),
                "sw_uploaded": out_date,
                "sw_version": client.get_software_commit(),
                "sw_branch": client.get_software_branch(),
                "port_mapping": client.get_port_mapping()}
