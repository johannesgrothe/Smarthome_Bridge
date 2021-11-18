import json
import os
from jsonschema import validate, ValidationError

from logging_interface import LoggingInterface


_schema_folder = "json_schemas"
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

        # TODO: Use schema loader from system/utils

        self._logger.info("Reloading Schema Data")
        buf_schemas = {}
        relevant_files = [file for file in os.listdir(_schema_folder)
                          if os.path.isfile(os.path.join(_schema_folder, file))
                          and file.endswith('.json')]
        for filename in relevant_files:
            with open(os.path.join(_schema_folder, filename)) as f:
                data = json.load(f)
                try:
                    del data["$schema"]
                except KeyError:
                    pass
                buf_schemas[filename[:-5]] = data

        fixed_schemas = True
        runs = 0
        while fixed_schemas and runs <= 15:
            runs += 1
            fixed_schemas = 0
            for schema_name in buf_schemas:
                old_schema = buf_schemas[schema_name]
                new_schema = self._fix_schema(old_schema, buf_schemas)
                if new_schema != old_schema:
                    buf_schemas[schema_name] = new_schema
                    fixed_schemas = True

        _schema_data = buf_schemas

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
