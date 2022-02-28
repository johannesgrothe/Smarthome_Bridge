from smarthome_bridge.network_manager import NetworkManager
from system.api_definitions import ApiURIs

TEST_SENDER = "unittest"


def send_test(connector: NetworkManager, receiver_name: str, payload: dict):
    response = connector.send_request(ApiURIs.test_echo.uri, receiver_name, payload)
    assert response is not None
    assert response.get_payload() == payload
    return


def send_split_test(connector: NetworkManager, receiver_name: str, payload: dict, part_max_len: int = 30):
    response = connector.send_request_split(ApiURIs.test_echo.uri, receiver_name, payload, part_max_size=part_max_len)
    assert response is not None
    assert response.get_payload() == payload
    return


def broadcast_test(connector: NetworkManager, payload: dict):
    responses = connector.send_broadcast(ApiURIs.test_echo.uri, payload)
    assert len(responses) >= 1
    assert responses[0].get_payload() == payload
    return


def broadcast_single_response_test(connector: NetworkManager, payload: dict):
    responses = connector.send_broadcast(ApiURIs.test_echo.uri, payload, max_responses=1)
    assert len(responses) == 1
    assert responses[0].get_payload() == payload
    return
