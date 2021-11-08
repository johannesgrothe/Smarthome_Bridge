import pytest

from gadgets.gadget_event_mapping import GadgetEventMapping

EVENT_ID = "l0lc0d3_"
EVENT_LIST = [(1, 1), (2, 1)]


@pytest.mark.event
def test_gadget_e_mapping():
    e_mapping = GadgetEventMapping(EVENT_ID, EVENT_LIST)
    assert e_mapping.get_id() == EVENT_ID
    assert e_mapping.get_list() == EVENT_LIST
