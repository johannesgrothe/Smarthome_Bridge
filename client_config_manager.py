import logging
import os
import json
from typing import Optional
from json_validator import Validator, ValidationError

from logging_interface import LoggingInterface

_config_path = "configs"
_validation_schema_name = "client_config"


class ConfigNotValidException(Exception):
    def __init__(self):
        super().__init__(f"Error validating config")


class ConfigAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__(f"Config is already existing")


class ClientConfigManager(LoggingInterface):

    _config_data: dict
    _validator: Validator

    def __init__(self):
        super().__init__()
        self._validator = Validator()
        self.reload()

    @staticmethod
    def _generate_filename_for_config(config: dict):
        return f"{config['name'].lower()}.json"

    def load_config_from_path(self, file_path: str) -> Optional[dict]:
        with open(file_path, 'r') as file_h:
            loaded_file = json.load(file_h)
            try:
                self._validator.validate(loaded_file, _validation_schema_name)
                if self.get_config(loaded_file["name"]) is not None:
                    self._logger.warning("Unable to load config: name doubled.")
                else:
                    self._logger.info(f"Loaded config '{loaded_file['name']}'")
                    return loaded_file
            except ValidationError:
                self._logger.warning(f"Could not load '{file_path}': Validation failed")
        return None

    def _get_filename_for_config(self, name: str) -> Optional[str]:
        for filename in self._config_data:
            config_data = self._config_data[filename]
            if config_data["name"] == name:
                return filename
        return None

    def get_config_names(self) -> list:
        out_list = []
        for filename in self._config_data:
            config_data = self._config_data[filename]
            out_list.append(config_data["name"])
        return out_list

    def get_config_filenames(self) -> list:
        out_list = []
        for filename in self._config_data:
            out_list.append(filename)
        return out_list

    def reload(self):
        self._config_data = {}
        for file_name in os.listdir(_config_path):
            data = self.load_config_from_path(os.path.join(_config_path, file_name))
            if data is not None:
                self._config_data[file_name] = data

    def delete_config_file(self, name: str):
        filename = self._get_filename_for_config(name)
        path = os.path.join(_config_path, filename)
        if os.path.isfile(path):
            os.remove(path)
        self.reload()

    def get_config(self, name: str) -> Optional[dict]:
        for filename in self._config_data:
            config_data = self._config_data[filename]
            if config_data["name"] == name:
                return config_data
        return None

    def write_config(self, config: dict, overwrite: bool = False):
        try:
            self._validator.validate(config, _validation_schema_name)
        except ValidationError:
            raise ConfigNotValidException
        config_name = config["name"]

        existing_file = self._get_filename_for_config(config_name)
        if existing_file is not None:
            if overwrite:
                self.delete_config_file(config_name)
            else:
                raise ConfigAlreadyExistsException

        with open(os.path.join(_config_path, self._generate_filename_for_config(config)), 'w') as file_h:
            json.dump(config, file_h)

        self.reload()
