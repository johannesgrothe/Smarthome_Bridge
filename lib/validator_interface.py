from utils.json_validator import Validator


class IValidator:

    _validator: Validator

    def __init__(self):
        super().__init__()
        self._validator = Validator()
