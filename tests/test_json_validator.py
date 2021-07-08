import pytest
from json_validator import Validator, ValidationError, SchemaDoesNotExistException

TEST_REQ_OK = {"sender": "me",
               "receiver": "you",
               "session_id": 1776,
               "payload": {}}
TEST_REQ_ERR = {"test_key": "yolokopter"}

REQ_SCHEMA_NAME = "request_basic_structure"
ILLEGAL_SCHEMA_NAME = "yolokopter"


@pytest.fixture
def validator():
    validator = Validator()
    yield validator


def test_mqtt_connector_send(validator: Validator):
    validation_error = None
    try:
        validator.validate(TEST_REQ_OK, REQ_SCHEMA_NAME)
    except ValidationError as e:
        validation_error = e
    assert validation_error is None

    validation_error = None
    try:
        validator.validate(TEST_REQ_ERR, REQ_SCHEMA_NAME)
    except ValidationError as e:
        validation_error = e

    assert validation_error is not None

    validation_error = None
    try:
        validator.validate(TEST_REQ_OK, ILLEGAL_SCHEMA_NAME)
    except SchemaDoesNotExistException as e:
        validation_error = e

    assert validation_error is not None
