from typing import Optional

from lib.logging_interface import ILogging
from network.request import Request


class ResponseCreator(ILogging):
    @classmethod
    def respond_with_error(cls, req: Request, err_type: str, message: str):
        message = message.replace("\"", "'")
        req.respond({"ack": False, "error_type": err_type, "message": message})
        cls._get_logger().error(f"{err_type}: {message}")

    @classmethod
    def respond_with_success(cls, req: Request, message: Optional[str] = None):
        out_payload = {"ack": True, "message": message}
        req.respond(out_payload)
        cls._get_logger().info(f"Responding with success to request: {req.get_path()}")
