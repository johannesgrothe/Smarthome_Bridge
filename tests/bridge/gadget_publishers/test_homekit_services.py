import pytest

from gadget_publishers.homekit.homekit_services import SwitchService


@pytest.mark.bridge
def test_homekit_switch_service():
    switch = SwitchService()
