from typing import Optional

from network.auth_container import AuthContainer
from network.request import Request
from test_helpers.dummy_network_connector import DummyNetworkManager
from utils.json_validator import Validator

TEST_USER = "testerinski"


class ReqTester:
    mock_user: str
    network: DummyNetworkManager
    credentials: Optional[AuthContainer]
    validator: Validator

    def __init__(self, network: DummyNetworkManager,
                 credentials: Optional[AuthContainer],
                 validator: Validator):
        self.network = network
        self.credentials = credentials
        self.validator = validator
        self.mock_user = TEST_USER

    def request_execute(self, uri: str, payload: dict) -> Request:
        self.network.mock_connector.mock_receive(uri,
                                                 TEST_USER,
                                                 payload,
                                                 auth=self.credentials)
        last_response = self.network.mock_connector.get_last_send_response()
        assert last_response is not None
        assert last_response.get_path() == uri
        return last_response

    def request_execute_error(self, uri: str, error: str, payload: dict):
        last_response = self.request_execute(uri, payload)
        self.validator.validate(last_response.get_payload(), "error_response")
        assert last_response.get_payload()["error_type"] == error

    def request_execute_status(self, uri: str, payload: dict):
        last_response = self.request_execute(uri, payload)
        self.validator.validate(last_response.get_payload(), "default_message")
        assert last_response.get_payload()["ack"] is True

    def request_execute_payload(self, uri: str, schema: Optional[str], reference_payload: Optional[dict],
                                payload: dict):
        last_response = self.request_execute(uri, payload)
        if schema is None and reference_payload is None:
            raise Exception("This Test tests nothing.")
        if schema is not None:
            self.validator.validate(last_response.get_payload(), schema)
        if reference_payload is not None:
            assert last_response.get_payload() == reference_payload
