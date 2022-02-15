import os
import argparse
import logging
from typing import Optional, Callable

from utils.repository_manager import RepositoryManager, RepositoryCloneException, RepositoryFetchException, \
    RepositoryCheckoutException, RepositoryPullException
from utils.pio_uploader import PioUploader, PioUploadException
from utils.repo_locker import RepoLocker

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]

repo_name = "Smarthome_ESP32"
repo_url = "https://github.com/johannesgrothe/{}.git".format(repo_name)
_repo_base_path = "../temp"

_general_exit_code = 0

_fetch_ok_code = 1
_fetch_fail_code = -1

_cloning_ok_code = 2
_cloning_fail_code = -2

_checkout_ok_code = 3
_checkout_fail_code = -3

_pull_ok_code = 4
_pull_fail_code = -4


class UploadFailedException(Exception):
    def __init__(self):
        super().__init__(f"Failed to upload the software to the client")


class ChipFlasher:

    _output_callback: CallbackFunction
    _max_delay: Optional[int] = None
    _logger: logging.Logger
    _locker: Optional[RepoLocker]

    def __init__(self, output_callback: CallbackFunction = None, max_delay: Optional[int] = None):
        self._output_callback = output_callback
        self._max_delay = max_delay
        self._logger = logging.getLogger("ChipFlasher")
        self._locker = None
        if not os.path.isdir(_repo_base_path):
            if os.path.isfile(_repo_base_path):
                raise Exception("Repository target path is a file")
            self._logger.info(f"Creating directory '{_repo_base_path}' in '{os.getcwd()}'")
            os.mkdir(_repo_base_path)

    def upload_software(self, branch: str, upload_port: Optional[str] = None, clone_new_repository: bool = False):
        with RepoLocker(_repo_base_path, self._max_delay) as self._locker:
            repo_manager = RepositoryManager(_repo_base_path, repo_name, repo_url)
            try:
                repo_manager.init_repository(force_reset=clone_new_repository, reclone_on_error=True)
                self._callback(_cloning_ok_code, "Cloning ok.")
            except RepositoryCloneException:
                self._callback(_cloning_fail_code, "Cloning failed.")
                raise UploadFailedException

            try:
                repo_manager.fetch()
                self._callback(_fetch_ok_code, "Fetching OK.")
            except RepositoryFetchException:
                self._callback(_fetch_fail_code, "Fetching failed.")
                raise UploadFailedException

            try:
                repo_manager.checkout(branch)
                self._callback(_checkout_ok_code, f"Checking out '{branch}' OK.")
            except RepositoryCheckoutException:
                self._callback(_checkout_fail_code, f"Checking out '{branch}' failed.")
                raise UploadFailedException

            try:
                repo_manager.pull()
                self._callback(_pull_ok_code, "Pulling was successful")
            except RepositoryPullException:
                self._callback(_pull_fail_code, f"Pulling failed.")
                raise UploadFailedException

            try:
                uploader = PioUploader(os.path.join(_repo_base_path, repo_name), self._callback)
                uploader.upload_software(upload_port)
            except PioUploadException:
                raise UploadFailedException

    def _callback(self, code: int, message: str):
        print(f"callback: {message}")
        if self._output_callback:
            self._output_callback("SOFTWARE_UPLOAD", code, message)

    @staticmethod
    def get_serial_ports() -> [str]:
        """Returns a list of all serial ports available to the system"""
        detected_ports = os.popen(f"ls /dev/tty*").read().strip("\n").split()
        valid_ports = []
        for port in detected_ports:
            if "usb" in port.lower():
                valid_ports.append(port)
        return valid_ports


def module_main():
    def callback(sender: str, code: int, message: str):
        print(f"{sender} | {code} | {message}")

    parser = argparse.ArgumentParser(description='Script to flash different software versions to the chip')
    parser.add_argument('--branch', help='git branch to flash on the chip')
    parser.add_argument('--serial_port', help='serial port for uploading')
    args = parser.parse_args()

    print("Launching Chip Flasher")
    branch = "develop"
    flasher = ChipFlasher(output_callback=callback)

    if args.branch:
        branch = args.branch
    if args.serial_port:
        flasher.upload_software(branch, args.serial_port)
    else:
        flasher.upload_software(branch)
    print("Done")


if __name__ == '__main__':
    module_main()
