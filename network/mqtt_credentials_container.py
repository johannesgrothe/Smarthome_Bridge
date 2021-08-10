from typing import Optional


class MqttCredentialsContainer:

    ip: str
    port: int
    username: Optional[str]
    password: Optional[str]

    def __init__(self, ip: str, port: int, username: Optional[str], password: Optional[str]):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def has_auth(self) -> bool:
        return self.username is not None and self.password is not None
