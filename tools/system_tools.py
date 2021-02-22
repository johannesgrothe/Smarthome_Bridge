"""Module to access information about the host system"""
import os
import re
from typing import Optional


def read_pio_version() -> Optional[str]:
    long_version_str = os.popen(f"pio --version").read()
    result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
    if result:
        return result[0][0]
    return None


def read_python_version() -> Optional[str]:
    long_version_str = os.popen(f"python --version").read()
    result = re.findall("Python ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
    if result:
        return result[0][0]
    return None


def read_pipenv_version() -> Optional[str]:
    long_version_str = os.popen(f"pipenv --version").read()
    result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
    if result:
        return result[0][0]
    return None


def read_git_version() -> Optional[str]:
    long_version_str = os.popen(f"git --version").read()
    result = re.findall("version ([0-9]+.[0-9]+(\\.[0-9]+)?)", long_version_str)
    if result:
        return result[0][0]
    return None


if __name__ == "__main__":
    print(read_pio_version())
    print(read_python_version())
    print(read_pipenv_version())
    print(read_git_version())
