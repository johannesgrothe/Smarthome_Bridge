from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.network_manager import NetworkManager


class RequestHandlerBridge(RequestHandler):

    def __init__(self, network: NetworkManager):
        super().__init__(network)

    def handle_request(self, req: Request) -> None:
        pass
