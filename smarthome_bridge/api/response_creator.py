from typing import Optional

from lib.logging_interface import ILogging
from network.request import Request


class ResponseCreator(ILogging):
    @staticmethod
    def _message_format(message: Optional[str]):
        if message:
            return message.replace("\"", "'")

    @classmethod
    def respond_with_error(cls, req: Request, err_type: str, message: Optional[str] = None):
        message = cls._message_format(message)
        req.respond({"ack": False,
                     "error_type": err_type,
                     "message": message})
        cls._get_logger().error(f"{err_type}: {message}")

    @classmethod
    def respond_with_success(cls, req: Request, message: Optional[str] = None):
        message = cls._message_format(message)
        req.respond({"ack": True,
                     "message": message})
        cls._get_logger().info(f"Responding with success to request: {req.get_path()}")
