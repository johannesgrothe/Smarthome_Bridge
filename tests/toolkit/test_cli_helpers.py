import pytest
import os
from toolkit.cli_helpers import ask_for_continue, enter_file_path, select_option


TEST_FILE_NAME = "test.log"
TEST_FILE_PATH = os.path.join("temp", TEST_FILE_NAME)
TEST_WRONG_PATH = os.path.join("temp", "non_exist")

TEST_OPTION_LIST = ["null", "ainz", "zwei"]


@pytest.fixture()
def buf_file():
    yield "tests/toolkit/test_cli_helpers.py"


def test_ask_for_continue(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda: 'y')
    result = ask_for_continue("Please select type 'y'")
    assert result is True

    inputs = iter(["", "yolo", "n"])
    monkeypatch.setattr('builtins.input', lambda: next(inputs))
    result = ask_for_continue("Please select type 'n'")
    assert result is False


def test_enter_file_path(buf_file: str, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda: buf_file)
    result = enter_file_path()
    assert result is buf_file

    monkeypatch.setattr('builtins.input', lambda: TEST_WRONG_PATH)
    result = enter_file_path()
    assert result is None


def test_select_option(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda: '0')
    result = select_option(TEST_OPTION_LIST)
    assert result == 0

    inputs = iter([len(TEST_OPTION_LIST), "-1", "yolo", "1"])
    monkeypatch.setattr('builtins.input', lambda: next(inputs))
    result = select_option(TEST_OPTION_LIST, "an option")
    assert result == 1

    monkeypatch.setattr('builtins.input', lambda: str(len(TEST_OPTION_LIST)))
    result = select_option(TEST_OPTION_LIST, back_option="back")
    assert result == -1
