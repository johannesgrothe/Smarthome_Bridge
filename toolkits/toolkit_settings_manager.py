import os
import json
import logging
from jsonschema import validate, ValidationError
from typing import Optional

_config_path = os.path.join("temp", "connection_configs.json")
_validation_schema_path = os.path.join("json_schemas", "toolkit_config.json")


class ValidationSchemaNotFoundException(Exception):
    def __init__(self):
        super().__init__(f"No schema for config validation found")


class ConfigAlreadyExistsException(Exception):
    def __init__(self, config_id: str):
        super().__init__(f"A config with the id '{config_id}' already exists")


class InvalidConfigException(Exception):
    def __init__(self, config_id: str):
        super().__init__(f"The config with the id '{config_id}' failed validation process")


class ToolkitSettingsManager:
    _logger: logging.Logger
    _configs: dict
    _validation_schema: dict

    def __init__(self):
        self._logger = logging.getLogger("ToolkitSettingsManager")
        self._load_validation_schema()
        self.load()

    def _load_validation_schema(self):
        try:
            with open(_validation_schema_path, 'r') as file_h:
                self._validation_schema = json.load(file_h)
        except IOError:
            self._logger.error("Validation scheme could not be loaded.")
            raise ValidationSchemaNotFoundException

    @staticmethod
    def _generate_base_config() -> dict:
        out_config = {"$schema": os.path.join("..", _validation_schema_path),
                      "bridge": {},
                      "mqtt": {}}
        return out_config

    def _config_is_valid(self, config_type: str, config_id: str, config: dict) -> bool:
        buf_config = self._generate_base_config()
        buf_config[config_type][config_id] = config
        try:
            validate(buf_config, self._validation_schema)
        except ValidationError:
            return False
        return True

    def load(self):
        try:
            with open(_config_path, 'r') as file_h:
                self._configs = json.load(file_h)
                self._logger.info("Config successfully loaded.")

        except IOError:
            self._logger.warning("No configs file found, creating new one.")
            self._configs = self._generate_base_config()
            self.save()

    def save(self):
        try:
            with open(_config_path, 'w') as file_h:
                json.dump(self._configs, file_h)
                self._logger.info("Saved config file to disk.")
        except IOError:
            self._logger.error("Could not save configs file.")

    def get_bridge_config_ids(self):
        return [config_id for config_id in self._configs["bridge"]]

    def get_bridge_config(self, config_id: str) -> Optional[dict]:
        try:
            return self._configs["bridge"][config_id]
        except KeyError:
            return None

    def set_bridge_config(self, config_id: str, config: dict, overwrite: bool = False):
        if not self._config_is_valid("bridge", config_id, config):
            raise InvalidConfigException(config_id)

        if config_id in self._configs["bridge"] and not overwrite:
            raise ConfigAlreadyExistsException(config_id)
        self._configs["bridge"][config_id] = config

    def get_mqtt_config_ids(self):
        return [config_id for config_id in self._configs["mqtt"]]

    def get_mqtt_config(self, config_id: str) -> Optional[dict]:
        try:
            return self._configs["mqtt"][config_id]
        except KeyError:
            return None

    def set_mqtt_config(self, config_id: str, config: dict, overwrite: bool = False):
        if not self._config_is_valid("mqtt", config_id, config):
            raise InvalidConfigException(config_id)

        if config_id in self._configs["mqtt"] and not overwrite:
            raise ConfigAlreadyExistsException(config_id)
        self._configs["mqtt"][config_id] = config
