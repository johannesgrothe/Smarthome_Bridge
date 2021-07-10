import os
import re
import argparse
import subprocess
import logging
import repository_manager
from typing import Optional, Callable

from repo_locker import RepoLocker, RepositoryAccessTimeout

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]
PioCallbackFunction = Optional[Callable[[int, str], None]]

repo_name = "Smarthome_ESP32"
repo_url = "https://github.com/johannesgrothe/{}.git".format(repo_name)
_repo_base_path = "temp"

_general_exit_code = 0

_fetch_ok_code = 1
_fetch_fail_code = -1

_cloning_ok_code = 2
_cloning_fail_code = -2

_checkout_ok_code = 3
_checkout_fail_code = -3

_pull_ok_code = 4
_pull_fail_code = -4

_connecting_ok_code = 5
_connecting_error_code = -5

_flash_ok_code = 6
_flash_fail_code = -6

_sw_upload_code = 8
_linking_code = 9
_compiling_framework_code = 10
_compiling_src_code = 11
_compiling_lib_code = 12
_writing_fw_code = 13
_ram_usage_code = 14


class PioCompileException(Exception):
    def __init__(self):
        super().__init__(f"Failed to compile sourcecode.")


class PioNoProjectFoundException(Exception):
    def __init__(self, path):
        super().__init__(f"The selected directory is no valid PlatformIO project directory: '{path}'")


class PioUploadException(Exception):
    def __init__(self):
        super().__init__(f"Failed to upload software.")


class UploadFailedException(Exception):
    def __init__(self):
        super().__init__(f"Failed to upload the software to the client")


class PioUploader:
    _project_path: str
    _output_callback: PioCallbackFunction
    _logger: logging.Logger

    # Upload message sent flags
    _compile_src_unsent: bool
    _compile_framework_unsent: bool
    _compile_lib_unsent: bool

    def __init__(self, project_path: str, output_callback: PioCallbackFunction = None):
        if not os.path.isfile(os.path.join(project_path, "platformio.ini")):
            raise PioNoProjectFoundException(project_path)
        self._project_path = project_path
        self._output_callback = output_callback
        self._logger = logging.getLogger("PioUploader")

    def _callback(self, code: int, message: str):
        if self._output_callback:
            self._output_callback(code, message)

    def _analyze_line(self, line: str):
        # Patterns
        link_pattern = "Linking .pio/build/[a-zA-Z0-9]+?/firmware.elf"
        ram_pattern = "RAM:.+?([0-9\\.]+?)%"
        flash_pattern = "Flash:.+?([0-9\\.]+?)%"
        connecting_pattern = "Serial port .+?"
        connecting_error_pattern = r"A fatal error occurred: \.+? Timed out waiting for packet header"
        writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"
        compile_src_pattern = r"Compiling .pio/build/\w+?/src/.+?.cpp.o"
        compile_framework_pattern = r"Compiling .pio/build/\w+?/FrameworkArduino/.+?.cpp.o"
        compile_lib_pattern = r"Compiling .pio/build/\w+?/lib[0-9]+/.+?.o"

        if re.findall(link_pattern, line):
            self._callback(_linking_code, "Linking...")

        elif re.findall(connecting_error_pattern, line):
            self._callback(_connecting_error_code, "Error connecting to Chip.")

        elif re.findall(connecting_pattern, line):
            self._callback(_connecting_ok_code, "Connecting to Chip...")

        elif re.findall(compile_src_pattern, line):
            if self._compile_src_unsent:
                self._callback(_compiling_src_code, "Compiling Source")
                self._compile_src_unsent = False

        elif re.findall(compile_framework_pattern, line):
            if self._compile_framework_unsent:
                self._callback(_compiling_framework_code, "Compiling Framework")
                self._compile_framework_unsent = False

        elif re.findall(compile_lib_pattern, line):
            if self._compile_lib_unsent:
                self._callback(_compiling_lib_code, "Compiling Libraries")
                self._compile_lib_unsent = False

        else:

            writing_group = re.match(writing_pattern, line)
            if writing_group:
                writing_address = int(writing_group.groups()[0], 16)
                percentage = writing_group.groups()[1]
                if writing_address >= 65536:
                    self._callback(_writing_fw_code, f"Writing Firmware: {percentage}%")

            ram_groups = re.match(ram_pattern, line)
            if ram_groups:
                ram = ram_groups.groups()[0]
                self._callback(_ram_usage_code, f"RAM usage: {ram}%")

            flash_groups = re.match(flash_pattern, line)
            if flash_groups:
                flash = flash_groups.groups()[0]
                self._callback(_sw_upload_code, f"Flash usage: {flash}%")

    def upload_software(self, port: str):

        self._compile_src_unsent = True
        self._compile_framework_unsent = True
        self._compile_lib_unsent = True

        upload_port_phrase = ""
        if port is not None:
            self._logger.info(f"Manually setting upload port to '{port}'")
            upload_port_phrase = f" --upload-port {port}"

        # Upload software
        upload_command = f"cd {self._project_path}; pio run --target upload{upload_port_phrase}"
        process = subprocess.Popen(upload_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        for raw_line in iter(process.stdout.readline, b''):
            line = raw_line.decode()
            self._analyze_line(line)
            # self._logger.info(line.strip("\n"))

        process.wait()
        if process.returncode != 0:
            self._callback(_flash_fail_code, f"Flashing failed.")
            raise PioUploadException
        self._callback(_flash_ok_code, "Flashing was successful.")


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

    def upload_software(self, branch: str, upload_port: Optional[str] = None, clone_new_repository: bool = False):
        with RepoLocker(_repo_base_path, self._max_delay) as self._locker:
            repo_manager = repository_manager.RepositoryManager(_repo_base_path, repo_name, repo_url)
            try:
                repo_manager.init_repository(force_reset=clone_new_repository)
                self._callback(_cloning_ok_code, "Cloning ok.")
            except repository_manager.RepositoryCloneException:
                self._callback(_cloning_fail_code, "Cloning failed.")
                raise UploadFailedException

            try:
                repo_manager.fetch()
                self._callback(_fetch_ok_code, "Fetching OK.")
            except repository_manager.RepositoryFetchException:
                self._callback(_fetch_fail_code, "Fetching failed.")
                raise UploadFailedException

            try:
                repo_manager.checkout(branch)
                self._callback(_checkout_ok_code, f"Checking out '{branch}' OK.")
            except repository_manager.RepositoryCheckoutException:
                self._callback(_checkout_fail_code, f"Checking out '{branch}' failed.")
                raise UploadFailedException

            try:
                repo_manager.pull()
                self._callback(_pull_ok_code, "Pulling was successful")
            except repository_manager.RepositoryPullException:
                self._callback(_pull_fail_code, f"Pulling failed.")
                raise UploadFailedException

            try:
                uploader = PioUploader(os.path.join(_repo_base_path, repo_name), self._callback)
                uploader.upload_software(upload_port)
            except (PioUploadException, PioCompileException):
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
