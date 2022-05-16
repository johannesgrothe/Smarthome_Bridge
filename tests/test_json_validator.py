import pytest
from jsonschema import ValidationError

from utils.json_validator import Validator, SchemaDoesNotExistError

TEST_REQ_OK = {"sender": "me",
               "receiver": "you",
               "session_id": 1776,
               "payload": {},
               "is_response": False}
TEST_REQ_ERR = {"test_key": "yolokopter"}

REQ_SCHEMA_NAME = "request_basic_structure"
ILLEGAL_SCHEMA_NAME = "yolokopter"


def dict_contains_key(search_key: str, json_obj: dict) -> bool:
    for key in json_obj:
        if key == search_key:
            return True
        else:
            if isinstance(json_obj[key], dict):
                return dict_contains_key(search_key, json_obj[key])
    return False


def test_json_validator(f_validator: Validator):
    f_validator.validate(TEST_REQ_OK, REQ_SCHEMA_NAME)

    with pytest.raises(ValidationError):
        f_validator.validate(TEST_REQ_ERR, REQ_SCHEMA_NAME)

    with pytest.raises(SchemaDoesNotExistError):
        f_validator.validate(TEST_REQ_OK, ILLEGAL_SCHEMA_NAME)


def test_json_validator_refs(f_validator: Validator):
    assert len(f_validator.get_schema_names()) > 0
    for schema_name in f_validator.get_schema_names():
        assert dict_contains_key("$ref", f_validator.get_schema(schema_name)) is False
        assert dict_contains_key("$schema", f_validator.get_schema(schema_name)) is False
