import pytest
from network_connector import NetworkConnector
from network_server import NetworkServer

TEST_PATH = "smarthome/unittest"

LOREM_IPSUM = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut " \
              "labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores " \
              "et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem " \
              "ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore " \
              "et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea " \
              "rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."

LOREM_IPSUM_SHORT = "Lorem ipsum, digga"


@pytest.fixture
def test_payload_big() -> dict:
    return {"data": 12345,
            "list": [1, 2, 3, 4, 5],
            "strings":
                {
                    "lorem_long": LOREM_IPSUM,
                    "lorem_short": LOREM_IPSUM_SHORT
                }
            }


@pytest.fixture
def test_payload_small() -> dict:
    return {"lorem": LOREM_IPSUM_SHORT}


def send_test(connector: NetworkConnector, receiver_name: str, payload: dict):
    response = connector.send_request(TEST_PATH, receiver_name, payload)
    assert response is not None
    assert response.get_payload() == payload
    return


def send_split_test(connector: NetworkConnector, receiver_name: str, payload: dict):
    response = connector.send_request_split(TEST_PATH, receiver_name, payload)
    assert response is not None
    assert response.get_payload() == payload
    return


def broadcast_test(connector: NetworkConnector, payload: dict):
    responses = connector.send_broadcast(TEST_PATH, payload)
    assert len(responses) >= 1
    assert responses[0].get_payload() == payload
    return


def broadcast_single_response_test(connector: NetworkConnector, payload: dict):
    responses = connector.send_broadcast(TEST_PATH, payload, max_responses=1)
    assert len(responses) == 1
    assert responses[0].get_payload() == payload
    return
