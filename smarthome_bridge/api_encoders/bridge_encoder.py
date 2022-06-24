from datetime import datetime
from typing import Tuple

from smarthome_bridge.api_encoders import DATETIME_FORMAT
from smarthome_bridge.bridge_information_container import BridgeInformationContainer


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
                "running_since": datetime.strftime(bridge_info.running_since, DATETIME_FORMAT),
                "platformio_version": bridge_info.pio_version,
                "git_version": bridge_info.git_version,
                "python_version": bridge_info.python_version,
                "pipenv_version": bridge_info.pipenv_version}

    @staticmethod
    def encode_bridge_update_info(update_info: Tuple[str, str, str, str, str, int]) -> dict:
        """
        Serializes bridge information according to api specification

        :param update_info: bridge update information
        :return:
        """
        curr_hash, new_hash, branch_name, curr_date, new_date, num_commits = update_info
        return {"current_commit_hash": curr_hash,
                "new_commit_hash": new_hash,
                "current_branch_name": branch_name,
                "current_branch_release_date": curr_date,
                "new_branch_release_date": new_date,
                "num_commits_between_branches": num_commits}
