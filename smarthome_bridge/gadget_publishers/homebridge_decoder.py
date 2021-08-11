from logging_interface import LoggingInterface


class HomebridgeDecoder(LoggingInterface):

    def __init__(self):
        super().__init__()

    def decode_gadget(self, name: str, data: dict):
        pass

    def _decode_fan(self, name: str, data: dict):
        pass
