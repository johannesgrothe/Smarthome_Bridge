from request import Request
from typing import Optional


class NetworkConnector:
    """Class to implement an network interface prototype"""

    def send_request(self, req: Request, timeout: int = 6) -> (Optional[bool], Optional[Request]):
        print("Not implemented")
        return None, None

    def send_broadcast(self, req: Request, timeout: int = 5) -> [Request]:
        print("Not implemented")
        return []
