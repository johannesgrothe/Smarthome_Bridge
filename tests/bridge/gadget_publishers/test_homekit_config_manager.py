import json
import os

import pytest

from gadget_publishers.homekit.homekit_config_manager import HomekitConfigManager, NoConfigFoundError


@pytest.fixture()
def manager(f_temp_exists):
    config_file = os.path.join(f_temp_exists, "test_config.json")
    manager = HomekitConfigManager(config_file)
    yield manager


@pytest.mark.bridge
def test_homekit_constants(manager: HomekitConfigManager):
    assert manager.data is None
    with pytest.raises(NoConfigFoundError):
        manager.reset_config_pairings()

    manager.generate_new_config()

    data = manager.data
    assert data is not None

    assert len(data["accessory_pairing_id"]) == 17
    assert len(data["accessory_pairing_id"].split(":")) == 6

    assert len(data["accessory_pin"]) == 10
    assert len(data["accessory_pin"].split("-")) == 3

    assert len(data["host_ip"].split(".")) == 4

    assert data["category"] == "Bridge"
    assert data["name"] == "Python_Smarthome_Bridge"
    assert isinstance(data["host_port"], int)

    manager.generate_new_config()

    new_data = manager.data

    for key in ["accessory_pairing_id", "accessory_pin"]:
        assert new_data[key] != data[key]

    for key in ["c#", "category", "host_ip", "host_port", "name"]:
        assert new_data[key] == data[key]

    manager.reset_config_pairings()

    with open(manager.path, "r") as file_p:
        loaded_file = json.load(file_p)

    del loaded_file["accessory_pairing_id"]

    with open(manager.path, "w") as file_p:
        json.dump(loaded_file, file_p)

    with pytest.raises(NoConfigFoundError):
        manager.reset_config_pairings()
