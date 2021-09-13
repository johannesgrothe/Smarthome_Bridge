"""Module to access information about the host system"""
import os
import re
from typing import Optional


class SystemInfoTools:

    @staticmethod
    def read_pio_version() -> Optional[str]:
        """
        Reads the platformio version from the host system
        The returned version string fits <int>.<int>(.<int>)

        :return: The version as string or none
        """
        long_version_str = os.popen(f"pio --version").read()
        result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
        if result:
            return result[0][0]
        return None

    @staticmethod
    def read_python_version() -> Optional[str]:
        """
        Reads the python version from the host system
        The returned version string fits <int>.<int>(.<int>)

        :return: The version as string or none
        """
        long_version_str = os.popen(f"python --version").read()
        result = re.findall("Python ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
        if result:
            return result[0][0]
        return None

    @staticmethod
    def read_pipenv_version() -> Optional[str]:
        """
        Reads the pipenv version from the host system
        The returned version string fits <int>.<int>(.<int>)

        :return: The version as string or none
        """
        long_version_str = os.popen(f"pipenv --version").read()
        result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
        if result:
            return result[0][0]
        return None

    @staticmethod
    def read_git_version() -> Optional[str]:
        """
        Reads the git version from the host system
        The returned version string fits <int>.<int>(.<int>)

        :return: The version as string or none
        """
        long_version_str = os.popen(f"git --version").read()
        result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
        if result:
            return result[0][0]
        return None


if __name__ == "__main__":
    print(f"pio: {SystemInfoTools.read_pio_version()}")
    print(f"python: {SystemInfoTools.read_python_version()}")
    print(f"pipenv: {SystemInfoTools.read_pipenv_version()}")
    print(f"git: {SystemInfoTools.read_git_version()}")
