class ClientEventMapping:
    _event_id: str
    _code_list: list[int]

    def __init__(self, event_id: str, code_list: list[int]):
        self._event_id = event_id
        self._code_list = code_list

    def __del__(self):
        pass

    def get_id(self) -> str:
        return self._event_id

    def get_codes(self) -> list[int]:
        return self._code_list
    