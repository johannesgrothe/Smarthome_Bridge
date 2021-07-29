import pytest
import random

from smarthome_bridge.serializer import Serializer
from smarthome_bridge.smarthomeclient import SmarthomeClient


CLIENT_NAME = "test_client"


@pytest.fixture()
def serializer():
    serializer = Serializer()
    yield serializer


@pytest.fixture()
def test_client():
    client = SmarthomeClient(CLIENT_NAME,
                             random.randint(0, 10000),
                             None,
                             None,
                             None,
                             {},
                             1)
    yield client
    # client.__del__()


@pytest.mark.bridge
def test_bridge(serializer: Serializer, test_client: SmarthomeClient):
    serialized_data = serializer.serialize_client(test_client)
    assert serialized_data != {}
