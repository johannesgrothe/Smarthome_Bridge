from typing import Optional


class MqttCredentialsError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class MqttCredentialsContainer:

    ip: str
    port: int
    username: Optional[str]
    password: Optional[str]

    def __init__(self, ip: str, port: int, username: Optional[str] = None, password: Optional[str] = None):
        try:
            if not isinstance(ip, str):
                raise ValueError()
        except ValueError:
            raise MqttCredentialsError(f"Illegal ip for MQTT credentials: '{ip}'")
        if not isinstance(port, int) or port < 0:
            raise MqttCredentialsError(f"Illegal port for MQTT credentials: '{port}'")
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def has_auth(self) -> bool:
        return self.username is not None and self.password is not None
