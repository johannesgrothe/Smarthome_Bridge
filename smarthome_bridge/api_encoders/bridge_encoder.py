from datetime import datetime
from typing import Tuple

from smarthome_bridge.api_encoders import DATETIME_FORMAT
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.update.bridge_update_manager import BridgeUpdateInformationContainer


class BridgeEncoder:

    @staticmethod
    def encode_bridge_info(bridge_info: BridgeInformationContainer) -> dict:
        """
        Serializes bridge information according to api specification

        :param bridge_info: Container for the bridge information
        :return:
        """
        return {"bridge_name": bridge_info.name,
                "software_commit": bridge_info.git_commit,
                "software_branch": bridge_info.git_branch,
                "running_since": bridge_info.running_since.strftime(DATETIME_FORMAT),
                "platformio_version": bridge_info.pio_version,
                "git_version": bridge_info.git_version,
                "python_version": bridge_info.python_version,
                "pipenv_version": bridge_info.pipenv_version}

    @staticmethod
    def encode_bridge_update_info(update_info: BridgeUpdateInformationContainer) -> dict:
        """
        Serializes bridge information according to api specification

        :param update_info: bridge update information
        :return:
        """
        return {"current_version": update_info.current_version,
                "current_date": update_info.current_date.strftime(DATETIME_FORMAT),
                "new_version": update_info.new_version,
                "new_date": update_info.new_date.strftime(DATETIME_FORMAT)}
