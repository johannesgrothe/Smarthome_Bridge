import pytest

from smarthome_bridge.client_event_mapping import ClientEventMapping

EVENT_ID = "ab09jo3r_"
EVENT_LIST = [1234, 5674]


@pytest.mark.event
def test_client_e_mapping():
    e_mapping = ClientEventMapping(EVENT_ID, EVENT_LIST)
    assert e_mapping.get_id() == EVENT_ID
    assert e_mapping.get_codes() == EVENT_LIST
