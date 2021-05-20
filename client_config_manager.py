import logging
import os
import json
from jsonschema import validate, ValidationError
from typing import Optional

_config_path = "configs"
_validation_scheme_path = "json_schemas/client_config.json"


class ValidationSchemaNotFoundException(Exception):
    def __init__(self):
        super().__init__(f"No Schema for config validation found")


class ConfigNotFoundException(Exception):
    def __init__(self, name: str):
        super().__init__(f"Config '{name}' was not found")


class ConfigNotValidException(Exception):
    def __init__(self):
        super().__init__(f"Error validating config")


class ConfigAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__(f"Config is already existing")


class ConfigDoubledException(Exception):
    def __init__(self):
        super().__init__(f"Two Configs with the same name are stored")


class ClientConfigManager:

    _config_schema: dict
    _schema_data: dict
    _logger: logging.Logger

    def __init__(self):
        self._logger = logging.getLogger("ClientConfigManager")
        self._load_validation_schema()
        self.reload()

    @staticmethod
    def _generate_filename_for_config(config: dict):
        return f"{config['name'].lower()}.json"

    def _load_validation_schema(self):
        try:
            with open(_validation_scheme_path, 'r') as file_h:
                self._config_schema = json.load(file_h)
        except OSError:
            self._logger.error("Could not load validation scheme")
            raise ValidationSchemaNotFoundException

    def load_config_from_path(self, file_path: str) -> Optional[dict]:
        with open(file_path, 'r') as file_h:
            loaded_file = json.load(file_h)
            try:
                validate(loaded_file, self._config_schema)
                if self.get_config(loaded_file["name"]) is not None:
                    self._logger.warning("Unable to load config: name doubled.")
                else:
                    self._logger.info(f"Loaded config '{loaded_file['name']}'")
                    return loaded_file
            except ValidationError:
                self._logger.warning(f"Could not load '{file_path}': Validation failed")
        return None

    def _get_filename_for_config(self, name: str) -> Optional[str]:
        for filename in self._schema_data:
            config_data = self._schema_data[filename]
            if config_data["name"] == name:
                return filename
        return None

    def get_config_names(self) -> list:
        out_list = []
        for filename in self._schema_data:
            config_data = self._schema_data[filename]
            out_list.append(config_data["name"])
        return out_list

    def get_config_filenames(self) -> list:
        out_list = []
        for filename in self._schema_data:
            out_list.append(filename)
        return out_list

    def reload(self):
        self._schema_data = {}
        for file_name in os.listdir(_config_path):
            data = self.load_config_from_path(os.path.join(_config_path, file_name))
            if data is not None:
                self._schema_data[file_name] = data

    def delete_config_file(self, filename: str):
        path = os.path.join(_config_path, filename)
        if os.path.isfile(path):
            os.remove(path)
        self.reload()

    def get_config(self, name: str) -> Optional[dict]:
        for filename in self._schema_data:
            config_data = self._schema_data[filename]
            if config_data["name"] == name:
                return config_data
        return None

    def write_config(self, config: dict, overwrite: bool = False):
        try:
            validate(config, self._config_schema)
        except ValidationError:
            raise ConfigNotValidException
        config_name = config["name"]

        existing_file = self._get_filename_for_config(config_name)
        if existing_file is not None:
            if overwrite:
                self.delete_config_file(existing_file)
            else:
                raise ConfigAlreadyExistsException

        with open(os.path.join(_config_path, self._generate_filename_for_config(config)), 'w') as file_h:
            json.dump(config, file_h)

        self.reload()
