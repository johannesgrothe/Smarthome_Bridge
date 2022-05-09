import pytest

from network.rest_server import RestServer


API_ADDRESS = "localhost"
API_PORT = 55


@pytest.fixture
def server():
    server = RestServer("rest_server", API_PORT)
    yield server
    server.__del__()


@pytest.mark.network
def test_rest_server_receive(server: RestServer):
    client = server._app.test_client()
    res = client.get("test")
    assert res.status_code == 200
