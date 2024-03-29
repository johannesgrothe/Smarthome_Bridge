import pytest
import time
from utils.loading_indicator import LoadingIndicator


@pytest.fixture
def indicator():
    indicator = LoadingIndicator()
    yield indicator


def test_loading_indicator(indicator: LoadingIndicator):
    exception_raised = False
    indicator.run()
    time.sleep(1.5)
    indicator.stop()
    with indicator:
        time.sleep(1.5)
    assert exception_raised is False
