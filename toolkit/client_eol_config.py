from typing_extensions import Self

from toolkit.config import Config, ConfigLoadingError
from variants import HwVariant


class ClientEolConfig(Config):
    _type_key = "eol"

    _variant: HwVariant
    _serial: str

    def __init__(self, variant: HwVariant, serial: str):
        self._variant = variant
        self._serial = serial

    @property
    def variant(self) -> HwVariant:
        return self._variant

    @property
    def serial(self) -> str:
        return self._serial

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "variant": self._variant.value,
            "serial": self._serial
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        try:
            cls._check_type_key(data)
            return cls(
                HwVariant(data["variant"]),
                data["serial"],
            )
        except (KeyError, ValueError) as e:
            raise ConfigLoadingError(f"Invalid client system config: {e}")
