import pytest
from lib.pubsub import Publisher, Subscriber
from typing import Optional
from network.request import Request

_received_request: Optional[Request] = None


class DummyPublisher(Publisher):
    def publish(self, req: Request):
        self._publish(req)


class DummySubscriber(Subscriber):
    def receive(self, req: Request):
        global _received_request
        _received_request = req


@pytest.fixture
def subscriber():
    subscriber = DummySubscriber()
    yield subscriber


@pytest.fixture
def publisher():
    publisher = DummyPublisher()
    yield publisher


@pytest.fixture
def test_req():
    req = Request("test_path",
                  1776,
                  "testsuite",
                  None,
                  {},
                  is_response=False)
    yield req


def test_pub_sub(subscriber: DummySubscriber, publisher: DummyPublisher, test_req: Request):
    global _received_request
    _received_request = None

    assert publisher.get_client_number() == 0
    publisher.subscribe(subscriber)
    assert publisher.get_client_number() == 1
    publisher.publish(test_req)
    assert _received_request == test_req
    publisher.unsubscribe(subscriber)
    assert publisher.get_client_number() == 0
    _received_request = None
    publisher.publish(test_req)
    assert _received_request is None
