from smarthome_bridge.network_manager import NetworkManager

TEST_PATH = "test"
TEST_SENDER = "unittest"


def send_test(connector: NetworkManager, receiver_name: str, payload: dict):
    response = connector.send_request(TEST_PATH, receiver_name, payload)
    assert response is not None
    assert response.get_payload() == payload
    return


def broadcast_test(connector: NetworkManager, payload: dict):
    responses = connector.send_broadcast(TEST_PATH, payload)
    assert len(responses) >= 1
    assert responses[0].get_payload() == payload
    return


def broadcast_single_response_test(connector: NetworkManager, payload: dict):
    responses = connector.send_broadcast(TEST_PATH, payload, max_responses=1)
    assert len(responses) == 1
    assert responses[0].get_payload() == payload
    return
