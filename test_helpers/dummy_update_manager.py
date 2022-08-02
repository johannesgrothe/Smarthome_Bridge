import datetime
from typing import Optional

from smarthome_bridge.update.bridge_update_manager import BridgeUpdateManager, BridgeUpdateInformationContainer


class DummyUpdateManager(BridgeUpdateManager):
    mock_exception: Optional[Exception]
    mock_update_container: BridgeUpdateInformationContainer
    mock_reboot: bool

    def __init__(self):
        super().__init__()
        self.mock_exception = None
        self.mock_reboot = False
        self.mock_update_container = BridgeUpdateInformationContainer(
            "1.0.0",
            datetime.datetime.strptime("2016-06-21 15:30:00", "%Y-%m-%d %H:%M:%S"),
            "2.1.4",
            datetime.datetime.strptime("2022-06-21 10:00:00", "%Y-%m-%d %H:%M:%S")
        )

    def check_for_update(self) -> BridgeUpdateInformationContainer:
        if self.mock_exception is not None:
            raise self.mock_exception
        return self.mock_update_container

    def execute_update(self) -> None:
        if self.mock_exception is not None:
            raise self.mock_exception

    def reboot(self) -> None:
        self.mock_reboot = True
