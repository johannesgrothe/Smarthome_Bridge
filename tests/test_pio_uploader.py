import pytest
from utils.pio_uploader import PioUploader, PioUploadException, PioNoProjectFoundException
import os
import time
from utils.repository_manager import RepositoryManager

_repo_base_path = "temp"
_repo_name = "Smarthome_ESP32"
_repo_url = "https://github.com/johannesgrothe/Smarthome_ESP32"
_upload_port = "no_port"

_message_received = False


def pio_test_callback(code: int, message: str):
    global _message_received
    _message_received = True


@pytest.mark.github_skip
def test_pio_uploader():
    global _message_received
    repo_manager = RepositoryManager(_repo_base_path, _repo_name, _repo_url)
    repo_manager.delete_folder()

    try:
        PioUploader(os.path.join(_repo_base_path, _repo_name))
    except PioNoProjectFoundException:
        pass
    else:
        assert False

    _message_received = False
    repo_manager.init_repository(force_reset=True)
    uploader = PioUploader(os.path.join(_repo_base_path, _repo_name),
                           output_callback=pio_test_callback)
    time.sleep(0.1)
    assert _message_received is False

    try:
        uploader.upload_software(_upload_port)
    except PioUploadException:
        pass
    else:
        assert False

    assert _message_received is True
