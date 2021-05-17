import datetime
import os
import re
import argparse
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable

# Declare Type of callback function for hinting
CallbackFunction = Optional[Callable[[str, int, str], None]]

repo_name = "Smarthome_ESP32"
repo_url = "https://github.com/johannesgrothe/{}.git".format(repo_name)
_repo_base_path = "temp"
_repo_lockfile_path = "repo.lock"

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


def get_serial_ports() -> [str]:
    """Returns a list of all serial ports available to the system"""
    detected_ports = os.popen(f"ls /dev/tty*").read().strip("\n").split()
    valid_ports = []
    for port in detected_ports:
        if "usb" in port.lower():
            valid_ports.append(port)
    return valid_ports

# TODO: Create Object for chip flasher
# TODO: Move cloned repository to temp/
# TODO: Create lock file to prevent other instance from accessing/manipulating the
#  existing repository before writing is finished


class RepositoryAccessTimeout(Exception):
    def __init__(self, timeout: int):
        super().__init__(f"Repository could not be accessed: Timeout of {timeout} seconds has passed")


class RepositoryFetchException(Exception):
    def __init__(self):
        super().__init__(f"Fetching repository failed.")


class RepoLocker:

    _max_delay: Optional[int]
    _has_repo_locked: bool

    def __init__(self, max_delay: Optional[int] = None):
        self._max_delay = max_delay
        self._has_repo_locked = False

    def __del__(self):
        self._release_repository_lock()

    def __enter__(self):
        self.lock_repository()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._release_repository_lock()

    def _write_repository_lock(self):
        if not self._has_repo_locked:
            with open(os.path.join(_repo_base_path, _repo_lockfile_path), 'w') as f:
                f.write('This is a lock file created by the chip flasher.\n'
                        'If you have any problems with the chip flasher module, '
                        'shut down all sunning instances and delete this file.')
            self._has_repo_locked = True

    def _release_repository_lock(self):
        if self._has_repo_locked:
            self._has_repo_locked = False
            os.remove(os.path.join(_repo_base_path, _repo_lockfile_path))

    def _wait_for_repository(self):
        """Waits for the cloned repository to be available (not used by any other process)"""
        start_time = datetime.now()
        while os.path.isfile(os.path.join(_repo_base_path, _repo_lockfile_path)):
            if self._max_delay is not None:
                if start_time + timedelta(seconds=self._max_delay) < datetime.now():
                    raise RepositoryAccessTimeout(self._max_delay)

    def lock_repository(self):
        self._wait_for_repository()
        self._write_repository_lock()


class ChipFlasher:

    _output_callback: CallbackFunction
    _max_delay: Optional[int] = None
    _logger: logging.Logger

    def __init__(self, output_callback: CallbackFunction = None, max_delay: Optional[int] = None):
        self._output_callback = output_callback
        self._max_delay = max_delay
        self._logger = logging.getLogger("ChipFlasher")

    def _callback(self, code: int, message: str):
        if self._output_callback:
            self._output_callback("SOFTWARE_UPLOAD", code, message)

    def _init_repository(self, force_reset: bool) -> bool:
        repo_works = False

        if force_reset:
            os.remove(repo_name)
        else:
            if os.path.isdir(repo_name):
                repo_clean = os.system(f"cd {repo_name};git diff --quiet") == 0
                repo_works = repo_clean

        if not repo_works:
            self._logger.info(f"Repo doesn't exist or is broken, Cloning repository from '{repo_url}'")
            repo_works = os.system("git clone {}".format(repo_url)) == 0
            os.system(f"cd {repo_name};git config pull.ff only")

        if not repo_works:
            self._logger.error("Error cloning repository")
            self._callback(_cloning_fail_code, "Cloning failed.")
            return False
        else:
            self._callback(_cloning_ok_code, "Cloning ok.")

    def _fetch_repository(self):
        with RepoLocker(self._max_delay):
            self._logger.info(f"Fetching repository")
            fetch_ok = os.system(f"cd {repo_name};git fetch") == 0
            if not fetch_ok:
                self._logger.error("Fetching repository failed.")
                self._callback(_fetch_fail_code, "Fetching failed.")
                raise RepositoryFetchException
            else:
                self._logger.info("Fetching repository was successful.")
                self._callback(_fetch_ok_code, "Fetching OK.")


def flash_chip(branch_name: str, force_reset: bool = False, upload_port: Optional[str] = None,
               output_callback: CallbackFunction = None) -> bool:
    res = flash_chip_helper(branch_name, force_reset, upload_port, output_callback)
    if output_callback:
        output_callback("SOFTWARE_UPLOAD", _general_exit_code, "Flashing process finished.")
    return res


def flash_chip_helper(b_name: str, f_reset: bool = False, upload_port: Optional[str] = None,
                      output_callback: CallbackFunction = None) -> bool:

    upload_port_phrase = ""
    if upload_port is not None:
        print("Manually setting upload port to '{}'".format(upload_port))
        upload_port_phrase = " --upload-port {}".format(upload_port)

    repo_works = False

    if f_reset:
        os.remove(repo_name)
    else:
        if os.path.isdir(repo_name):

            # Fetch branch
            print(f"Fetching '{b_name}'")
            fetch_ok = os.system(f"cd {repo_name};git fetch") == 0
            if not fetch_ok:
                print("Failed.")
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD", _fetch_fail_code, "Fetching failed.")
                os.remove(repo_name)
            else:
                repo_works = True
                print("Ok.\n")
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD", _fetch_ok_code, "Fetching OK.")

    if not repo_works:
        print(f"Repo doesn't exist or is broken.\nCloning repository from '{repo_url}'")
        repo_works = os.system("git clone {}".format(repo_url)) == 0
        os.system(f"cd {repo_name};git config pull.ff only")

    if not repo_works:
        print("Error cloning repository")
        if output_callback:
            output_callback("SOFTWARE_UPLOAD", _cloning_fail_code, "Cloning failed.")
        return False
    else:
        if output_callback:
            output_callback("SOFTWARE_UPLOAD", _cloning_ok_code, "Cloning ok.")

    # Check out selected branch
    print(f"Checking out '{b_name}':")
    checkout_successful = os.system(f"cd {repo_name};git checkout {b_name}") == 0
    if not checkout_successful:
        print("Failed.")
        if output_callback:
            output_callback("SOFTWARE_UPLOAD", _checkout_fail_code, f"Checking out '{b_name}' failed.")
        return False
    print("Ok.\n")
    if output_callback:
        output_callback("SOFTWARE_UPLOAD", _checkout_ok_code, f"Checking out '{b_name}' OK.")

    # Pull branch
    print(f"Pulling '{b_name}'")
    pull_ok = os.system(f"cd {repo_name};git pull") == 0
    if not pull_ok:
        print("Failed.")
        if output_callback:
            output_callback("SOFTWARE_UPLOAD", _pull_fail_code, f"Pulling '{b_name}' failed.")
    print("Ok.\n")
    if output_callback:
        output_callback("SOFTWARE_UPLOAD", _pull_ok_code, f"Pulling '{b_name}' OK.")

    # Get double check data
    b_name = os.popen(f"cd {repo_name};git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)") \
        .read().strip("\n")
    commit_hash = os.popen(f"cd {repo_name};git rev-parse HEAD").read().strip("\n")
    print(f"Flashing branch '{b_name}', commit '{commit_hash}'")
    print()
    if output_callback:
        output_callback("SOFTWARE_UPLOAD",
                        _sw_upload_code,
                        f"Flashing branch '{b_name}', commit '{commit_hash}'")

    # Upload software
    upload_command = f"cd {repo_name}; pio run --target upload{upload_port_phrase}"
    process = subprocess.Popen(upload_command, stdout=subprocess.PIPE, shell=True)

    # Analyze output
    link_pattern = "Linking .pio/build/[a-zA-Z0-9]+?/firmware.elf"
    ram_pattern = "RAM:.+?([0-9\\.]+?)%"
    flash_pattern = "Flash:.+?([0-9\\.]+?)%"
    connecting_pattern = "Serial port .+?"
    connecting_error_pattern = r"A fatal error occurred: \.+? Timed out waiting for packet header"
    writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"

    compile_src_pattern = r"Compiling .pio/build/\w+?/src/.+?.cpp.o"
    compile_src_unsent = True

    compile_framework_pattern = r"Compiling .pio/build/\w+?/FrameworkArduino/.+?.cpp.o"
    compile_framework_unsent = True

    compile_lib_pattern = r"Compiling .pio/build/\w+?/lib[0-9]+/.+?.o"
    compile_lib_unsent = True

    for raw_line in iter(process.stdout.readline, b''):
        line = raw_line.decode()
        if re.findall(link_pattern, line):
            if output_callback:
                output_callback("SOFTWARE_UPLOAD", _linking_code, "Linking...")
        elif re.findall(connecting_error_pattern, line):
            if output_callback:
                output_callback("SOFTWARE_UPLOAD", _connecting_error_code, "Error connecting to Chip.")
        elif re.findall(connecting_pattern, line):
            if output_callback:
                output_callback("SOFTWARE_UPLOAD", _connecting_ok_code, "Connecting to Chip...")
        elif re.findall(compile_src_pattern, line):
            if compile_src_unsent:
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD", _compiling_src_code, "Compiling Source")
                compile_src_unsent = False
        elif re.findall(compile_framework_pattern, line):
            if compile_framework_unsent:
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD", _compiling_framework_code, "Compiling Framework")
                compile_framework_unsent = False
        elif re.findall(compile_lib_pattern, line):
            if compile_lib_unsent:
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD", _compiling_lib_code, "Compiling Libraries")
                compile_lib_unsent = False

        writing_group = re.match(writing_pattern, line)
        if writing_group:
            writing_address = int(writing_group.groups()[0], 16)
            percentage = writing_group.groups()[1]
            if writing_address >= 65536:
                if output_callback:
                    output_callback("SOFTWARE_UPLOAD",
                                    _writing_fw_code,
                                    f"Writing Firmware: {percentage}%")

        ram_groups = re.match(ram_pattern, line)
        if ram_groups:
            ram = ram_groups.groups()[0]
            if output_callback:
                output_callback("SOFTWARE_UPLOAD",
                                _ram_usage_code,
                                f"RAM usage: {ram}%")

        flash_groups = re.match(flash_pattern, line)
        if flash_groups:
            flash = flash_groups.groups()[0]
            if output_callback:
                output_callback("SOFTWARE_UPLOAD",
                                _sw_upload_code,
                                f"Flash usage: {flash}%")

        print(line.strip("\n"))

    process.wait()
    if process.returncode == 0:
        if output_callback:
            output_callback("SOFTWARE_UPLOAD",
                            _flash_ok_code,
                            "Flashing was successful.")
        return True
    if output_callback:
        output_callback("SOFTWARE_UPLOAD",
                        _flash_fail_code,
                        f"Flashing failed.")
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to flash different software versions to the chip')
    parser.add_argument('--branch', help='git branch to flash on the chip')
    parser.add_argument('--serial_port', help='serial port for uploading')
    ARGS = parser.parse_args()

    print("Launching Chip Flasher")
    branch = "develop"
    if ARGS.branch:
        branch = ARGS.branch
    if ARGS.serial_port:
        flash_chip(branch,
                   upload_port=ARGS.serial_port)
    else:
        flash_chip(branch)
    print("Done")
