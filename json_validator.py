import json
import os
from jsonschema import validate, ValidationError

from logging_interface import LoggingInterface

from system.utils.schema_loader import SchemaLoader


_schema_folder = os.path.join("system", "json_schemas")
_schema_data: dict = {}  # Schemas do not change at runtime, therefore all Validators can share the same dataset


class SchemaDoesNotExistError(Exception):
    def __init__(self, schema_name: str):
        super().__init__(f"Schema with the name '{schema_name}' does not exist.")


class Validator(LoggingInterface):

    def __init__(self):
        super().__init__()
        global _schema_data
        if not _schema_data:
            self.reload_schemas()

    def reload_schemas(self):
        """
        Reloads all the schema data from the disk and resolves the references

        :return: None
        """
        global _schema_data
        self._logger.info("Reloading Schema Data")
        loader = SchemaLoader(_schema_folder)
        _schema_data = loader.load_schemas()

    @staticmethod
    def get_schema(name: str):
        """
        Returns a copy with of the schema saved under the given name

        :param name: Name of the schema to return
        :return: A copy of the schema with the given name
        :raises SchemaDoesNotExistError: If no schema with the given name could be found
        """
        global _schema_data
        try:
            out_schema = _schema_data[name].copy()
            return out_schema
        except KeyError:
            raise SchemaDoesNotExistError(name)

    @staticmethod
    def get_schema_names() -> list[str]:
        """
        Returns the list of all schema names loaded at the moment

        :return: A list of all schema names
        """
        global _schema_data
        return [x for x in _schema_data.keys()]

    def _fix_schema(self, schema: dict, schema_list: dict) -> dict:
        buf_schema = schema.copy()
        for key in buf_schema:
            if key == "$ref":
                try:
                    schema_name = buf_schema[key][:-5]
                    return schema_list[schema_name]
                except KeyError:
                    return buf_schema
            elif isinstance(buf_schema[key], dict):
                buf_schema[key] = self._fix_schema(buf_schema[key], schema_list)
        return buf_schema

    @staticmethod
    def validate(target: dict, schema_name: str):
        """
        Validates a dict with the data from the given schema name

        :param target: Target dict to validate
        :param schema_name: The name of the schema used for validation
        :return: None
        :raises ValidationError: If the validation fails
        :raises SchemaDoesNotExistError: If schema with the given name can not be found
        """
        global _schema_data
        try:
            validate(target, _schema_data[schema_name])
        except KeyError:
            raise SchemaDoesNotExistError(f"Schema '{schema_name}' does not exist.")
