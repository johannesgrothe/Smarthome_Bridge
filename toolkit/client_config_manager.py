import os
import json
from pathlib import Path
from typing import Optional

from lib.logging_interface import ILogging
from toolkit.client_eol_config import ClientEolConfig
from toolkit.client_system_config import ClientSystemConfig
from toolkit.config import ConfigLoadingError, Config, WrongConfigTypeError


class ConfigNotValidException(Exception):
    def __init__(self):
        super().__init__(f"Error validating config")


class ConfigAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__(f"Config already exists")


class ConfigDoesNotExistException(Exception):
    def __init__(self, name: str):
        super().__init__(f"Config {name} does not exist")


class ClientConfigManager(ILogging):
    _config_data: dict
    _directory: Path

    def __init__(self, directory: Path):
        super().__init__()
        self._directory = directory
        if not os.path.isdir(self._directory):
            os.mkdir(self._directory)
        self.reload()

    @staticmethod
    def _generate_filename_for_config(config: dict):
        return f"{config['name'].lower()}.json"

    @classmethod
    def _load_config_from_path(cls, file_path: str) -> Config:
        with open(file_path, 'r') as file_h:
            loaded_file: dict = json.load(file_h)
        for config_type in [ClientEolConfig, ClientSystemConfig]:
            try:
                return config_type.from_dict(loaded_file)
            except WrongConfigTypeError:
                pass
        raise ConfigLoadingError(f"Unknown config type: {loaded_file.get('type', None)}")

    def get_config_filenames(self) -> list:
        return list(self._config_data.keys())

    def get_config_filenames_for(self, type_identifier: str) -> list[str]:
        return [file for file, config
                in self._config_data.items()
                if config.get_type_identifier() == type_identifier]

    def reload(self):
        self._config_data = {}
        for file_name in os.listdir(self._directory):
            try:
                cfg = self._load_config_from_path(os.path.join(self._directory, file_name))
                self._config_data[file_name] = cfg
            except ConfigLoadingError as err:
                self._logger.warning(f"Could not load config: {file_name}: {err}")

    def delete_config_file(self, filename: str):
        path = os.path.join(self._directory, filename)
        if os.path.isfile(path):
            os.remove(path)
        self.reload()

    def get_config(self, filename: str) -> Config:
        try:
            return self._config_data[filename]
        except KeyError:
            raise ConfigDoesNotExistException(filename)

    def write_config(self, config: Config, filename: str, overwrite: bool = False):
        if filename not in self._config_data:
            pass
        else:
            if overwrite:
                self.delete_config_file(filename)
            else:
                raise ConfigAlreadyExistsException()

        with open(self._directory / filename, 'w') as file_h:
            json.dump(config.to_dict(), file_h)

        self.reload()
