
class GadgetEventMapping:
    _event_id: str
    _event_list: list[tuple[int, int]]

    def __init__(self, event_id: str, event_list: list[tuple[int, int]]):
        self._event_id = event_id
        self._event_list = event_list

    def __del__(self):
        pass

    def get_id(self) -> str:
        return self._event_id

    def get_list(self) -> list[tuple[int, int]]:
        return self._event_list


