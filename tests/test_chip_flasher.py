import pytest
from chip_flasher import ChipFlasher, UploadFailedException

_software_branch = "develop"
_broken_branch = "no.branch"
_upload_port = "no_port"
_message_received = False


def flasher_test_callback(module: str, code: int, message: str):
    global _message_received
    _message_received = True


@pytest.mark.github_skip
def test_chip_flasher():
    flasher = ChipFlasher(flasher_test_callback, 5)
    assert flasher.get_serial_ports() is not None

    try:
        flasher.upload_software(_software_branch, _upload_port, clone_new_repository=True)
    except UploadFailedException:
        pass
    else:
        assert False

    try:
        flasher.upload_software(_broken_branch, _upload_port, clone_new_repository=False)
    except UploadFailedException:
        pass
    else:
        assert False
