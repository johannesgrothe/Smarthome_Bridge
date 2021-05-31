import json
import os
from typing import Optional
from jsonschema import validate, ValidationError


_schema_folder = "json_schemas"


class SchemaDoesNotExistException(Exception):
    def __init__(self, schema_name: str):
        super().__init__(f"Schema with the name '{schema_name}' does not exist.")


class Validator:

    _schema_data: dict

    def __init__(self):
        self.reload_schemas()

    def reload_schemas(self):
        buf_schemas = {}
        relevant_files = [file for file in os.listdir(_schema_folder)
                          if os.path.isfile(os.path.join(_schema_folder, file))
                          and file.endswith('.json')]
        for filename in relevant_files:
            with open(os.path.join(_schema_folder, filename)) as f:
                data = json.load(f)
                buf_schemas[filename[:-5]] = data
        self._schema_data = buf_schemas

    def validate(self, target: dict, schema_name: str):
        try:
            validate(target, self._schema_data[schema_name])
            return True
        except KeyError:
            raise SchemaDoesNotExistException
