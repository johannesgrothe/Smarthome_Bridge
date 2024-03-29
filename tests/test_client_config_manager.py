import pytest
from utils.client_config_manager import *

CONFIG_PATH = "configs"
VALID_CONFIG_NAME = "example"
TEST_CONFIG_NAME = "unittest_config"
DUMMY_BROKEN_CONFIG_NAME = "unittest_broken"
DUMMY_DOUBLE_CONFIG_NAME = "unittest_double"
INVALID_CONFIG = {"name": TEST_CONFIG_NAME, "status": "invalid u fuck"}

BROKEN_CFG_PATH = os.path.join(CONFIG_PATH, DUMMY_BROKEN_CONFIG_NAME + ".json")
DOUBLE_CFG_PATH = os.path.join(CONFIG_PATH, DUMMY_DOUBLE_CONFIG_NAME + ".json")


@pytest.fixture
def test_config():
    with open(os.path.join(CONFIG_PATH, VALID_CONFIG_NAME + ".json"), "r") as file_h:
        config = json.load(file_h)
        config["name"] = TEST_CONFIG_NAME
    yield config


@pytest.fixture
def dummy_files(test_config: dict):
    remove_test_configs()

    with open(os.path.join(CONFIG_PATH, VALID_CONFIG_NAME + ".json"), "r") as file_h:
        loaded_config = json.load(file_h)

    with open(BROKEN_CFG_PATH, "w") as file_h:
        json.dump(INVALID_CONFIG, file_h)

    with open(DOUBLE_CFG_PATH, "w") as file_h:
        json.dump(loaded_config, file_h)

    yield None

    remove_test_configs()


def remove_test_configs():
    try:
        os.remove(os.path.join(CONFIG_PATH, TEST_CONFIG_NAME + ".json"))
    except FileNotFoundError:
        pass

    try:
        os.remove(BROKEN_CFG_PATH)
    except FileNotFoundError:
        pass

    try:
        os.remove(DOUBLE_CFG_PATH)
    except FileNotFoundError:
        pass


def test_client_config_manager(dummy_files, f_config_manager: ClientConfigManager, test_config: dict):
    assert TEST_CONFIG_NAME not in f_config_manager.get_config_names()
    with pytest.raises(ConfigDoesNotExistException):
        f_config_manager.get_config(TEST_CONFIG_NAME)

    with pytest.raises(ConfigNotValidException):
        f_config_manager.write_config(INVALID_CONFIG)

    assert TEST_CONFIG_NAME not in f_config_manager.get_config_names()
    with pytest.raises(ConfigDoesNotExistException):
        f_config_manager.get_config(TEST_CONFIG_NAME)

    f_config_manager.write_config(test_config, overwrite=False)

    assert TEST_CONFIG_NAME in f_config_manager.get_config_names()
    assert TEST_CONFIG_NAME + ".json" in f_config_manager.get_config_filenames()
    buf_config = f_config_manager.get_config(TEST_CONFIG_NAME)
    assert buf_config is not None
    assert buf_config["name"] == TEST_CONFIG_NAME

    with pytest.raises(ConfigAlreadyExistsException):
        f_config_manager.write_config(test_config, overwrite=False)

    f_config_manager.write_config(test_config, overwrite=True)
