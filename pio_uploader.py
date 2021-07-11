
import re
import os
import logging
import subprocess
from typing import Optional, Callable

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


PioCallbackFunction = Optional[Callable[[int, str], None]]


class PioNoProjectFoundException(Exception):
    def __init__(self, path):
        super().__init__(f"The selected directory is no valid PlatformIO project directory: '{path}'")


class PioUploadException(Exception):
    def __init__(self):
        super().__init__(f"Failed to upload software.")


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
