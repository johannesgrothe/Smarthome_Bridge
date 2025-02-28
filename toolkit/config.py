class WrongConfigTypeError(Exception):
    pass


class ConfigLoadingError(Exception):
    pass


class Config:
    _type_key: str

    @classmethod
    def get_type_identifier(cls) -> str:
        return cls._type_key

    @classmethod
    def _check_type_key(cls, data: dict):
        if data["type"] != cls._type_key:
            raise WrongConfigTypeError(f"Config to be loaded is of the wrong type: {data['type']}")

    def to_dict(self) -> dict:
        return {"type": self._type_key}
