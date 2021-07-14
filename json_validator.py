import json
import logging
import os
from jsonschema import validate, ValidationError


_schema_folder = "json_schemas"
_schema_data: dict = {}  # Schemas do not change at runtime, therefore all Validators can share the same dataset


class SchemaDoesNotExistException(Exception):
    def __init__(self, schema_name: str):
        super().__init__(f"Schema with the name '{schema_name}' does not exist.")


class Validator:

    _logger: logging.Logger

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        global _schema_data
        if not _schema_data:
            self.reload_schemas()

    def reload_schemas(self):
        global _schema_data

        self._logger.info("Reloading Schema Data")
        buf_schemas = {}
        relevant_files = [file for file in os.listdir(_schema_folder)
                          if os.path.isfile(os.path.join(_schema_folder, file))
                          and file.endswith('.json')]
        for filename in relevant_files:
            with open(os.path.join(_schema_folder, filename)) as f:
                data = json.load(f)
                buf_schemas[filename[:-5]] = data
        _schema_data = buf_schemas

    @staticmethod
    def validate(target: dict, schema_name: str):
        global _schema_data
        try:
            validate(target, _schema_data[schema_name])
        except KeyError:
            raise SchemaDoesNotExistException(f"Schema '{schema_name}' does not exist.")
