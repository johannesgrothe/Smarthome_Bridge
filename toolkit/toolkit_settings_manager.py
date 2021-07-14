import os
import json
import logging
from json_validator import Validator, ValidationError
from typing import Optional

CONFIG_PATH = os.path.join("temp", "connection_configs.json")
VALIDATION_SCHEMA_NAME = "toolkit_config.json"
VALIDATION_SCHEMA_PATH = os.path.join("json_schemas", VALIDATION_SCHEMA_NAME)


class ConfigAlreadyExistsException(Exception):
    def __init__(self, config_id: str):
        super().__init__(f"A config with the id '{config_id}' already exists")


class InvalidConfigException(Exception):
    def __init__(self, config_id: str):
        super().__init__(f"The config with the id '{config_id}' failed validation process")


class ToolkitSettingsManager:
    _logger: logging.Logger
    _configs: dict
    _validator: Validator

    def __init__(self):
        self._logger = logging.getLogger("ToolkitSettingsManager")
        self._validator = Validator()
        self.load()

    @staticmethod
    def _generate_base_config() -> dict:
        out_config = {"$schema": os.path.join("..", VALIDATION_SCHEMA_PATH),
                      "bridge": {},
                      "mqtt": {}}
        return out_config

    def _config_is_valid(self, config_type: str, config_id: str, config: dict) -> bool:
        buf_config = self._generate_base_config()
        buf_config[config_type][config_id] = config
        try:
            self._validator.validate(buf_config, VALIDATION_SCHEMA_NAME)
        except ValidationError:
            return False
        return True

    def load(self):
        try:
            with open(CONFIG_PATH, 'r') as file_h:
                self._configs = json.load(file_h)
                self._logger.info("Config successfully loaded.")

        except IOError:
            self._logger.warning("No configs file found, creating new one.")
            self._configs = self._generate_base_config()
            self.save()

    def save(self):
        try:
            with open(CONFIG_PATH, 'w') as file_h:
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
