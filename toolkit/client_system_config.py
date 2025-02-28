from typing import Optional, Dict
from typing_extensions import Self

from toolkit.config import Config, ConfigLoadingError


class ClientSystemConfig(Config):
    _type_key = "system"

    _id: str
    _wifi_ssid: Optional[str]
    _wifi_pw: Optional[str]
    _mqtt_ip: Optional[str]
    _mqtt_port: Optional[int]
    _mqtt_username: Optional[str]
    _mqtt_password: Optional[str]

    def __init__(self,
                 id: str,
                 wifi_ssid: Optional[str],
                 wifi_pw: Optional[str],
                 mqtt_ip: Optional[str],
                 mqtt_port: Optional[int],
                 mqtt_username: Optional[str],
                 mqtt_password: Optional[str]):
        self._id = id
        self._wifi_ssid = wifi_ssid
        self._wifi_pw = wifi_pw
        self._mqtt_ip = mqtt_ip
        self._mqtt_port = mqtt_port
        self._mqtt_username = mqtt_username
        self._mqtt_password = mqtt_password

    @property
    def id(self) -> str:
        return self._id

    @property
    def wifi_ssid(self) -> Optional[str]:
        return self._wifi_ssid

    @property
    def wifi_pw(self) -> Optional[str]:
        return self._wifi_pw

    @property
    def mqtt_ip(self) -> Optional[str]:
        return self._mqtt_ip

    @property
    def mqtt_port(self) -> Optional[int]:
        return self._mqtt_port

    @property
    def mqtt_username(self) -> Optional[str]:
        return self._mqtt_username

    @property
    def mqtt_password(self) -> Optional[str]:
        return self._mqtt_password

    def to_dict(self) -> Dict[str, Optional[str]]:
        return super().to_dict() | {
            "id": self._id,
            "wifi_ssid": self._wifi_ssid,
            "wifi_pw": self._wifi_pw,
            "mqtt_ip": self._mqtt_ip,
            "mqtt_port": self._mqtt_port,
            "mqtt_username": self._mqtt_username,
            "mqtt_password": self._mqtt_password,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Optional[str]]) -> Self:
        try:
            cls._check_type_key(data)
            return cls(
                id=data["id"],
                wifi_ssid=data.get("wifi_ssid"),
                wifi_pw=data.get("wifi_pw"),
                mqtt_ip=data["mqtt_ip"],
                mqtt_port=int(data["mqtt_port"]) if data.get("mqtt_port") else None,
                mqtt_username=data.get("mqtt_username"),
                mqtt_password=data.get("mqtt_password"),
            )
        except (KeyError, ValueError) as e:
            raise ConfigLoadingError(f"Invalid client system config: {e}")
