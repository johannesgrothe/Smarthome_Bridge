from typing import Optional


class HomeBridgeRequest:
    topic: str
    message: dict

    def __init__(self, topic: str, message: dict):
        self.topic = topic
        self.message = message
        if "request_id" not in self.message:
            self.message["request_id"] = 0

    def set_request_id(self, req_id: int):
        self.message["request_id"] = req_id

    def get_request_id(self) -> int:
        return self.message["request_id"]

    def get_ack(self) -> Optional[bool]:
        if "ack" not in self.message:
            return None
        return self.message["ack"]
