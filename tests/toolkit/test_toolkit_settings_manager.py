import pytest
from toolkit.toolkit_settings_manager import *


@pytest.fixture()
def manager():
    manager = ToolkitSettingsManager()
    yield manager


def test_toolkit_settings_manager_bridge_configs(manager: ToolkitSettingsManager):
    configs = manager.get_bridge_config_ids()
    config = manager.get_bridge_config("testblub")
    assert config is None
