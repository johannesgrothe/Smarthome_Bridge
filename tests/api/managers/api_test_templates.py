from typing import Optional

from network.auth_container import AuthContainer
from network.request import Request
from test_helpers.dummy_network_connector import DummyNetworkManager
from utils.json_validator import Validator

TEST_USER = "testerinski"


def request_execute(uri: str, payload: dict, network: DummyNetworkManager,
                    credentials: Optional[AuthContainer]) -> Request:
    network.mock_connector.mock_receive(uri,
                                        TEST_USER,
                                        payload,
                                        auth=credentials)
    last_response = network.mock_connector.get_last_send_response()
    assert last_response is not None
    assert last_response.get_path() == uri
    return last_response


def request_execute_error(uri: str, error: str, payload: dict, network: DummyNetworkManager,
                          credentials: Optional[AuthContainer],
                          validator: Validator):
    last_response = request_execute(uri, payload, network, credentials)
    validator.validate(last_response.get_payload(), "error_response")
    assert last_response.get_payload()["error_type"] == error


def request_execute_status(uri: str, payload: dict, network: DummyNetworkManager,
                           credentials: Optional[AuthContainer],
                           validator: Validator):
    last_response = request_execute(uri, payload, network, credentials)
    validator.validate(last_response.get_payload(), "default_message")
    assert last_response.get_payload()["ack"] is True


def request_execute_payload(uri: str, schema: Optional[str], reference_payload: Optional[dict], payload: dict,
                            network: DummyNetworkManager, credentials: Optional[AuthContainer], validator: Validator):
    last_response = request_execute(uri, payload, network, credentials)
    if schema is None and reference_payload is None:
        raise Exception("This Test tests nothing.")
    if schema is not None:
        validator.validate(last_response.get_payload(), schema)
    if reference_payload is not None:
        assert last_response.get_payload() == reference_payload
