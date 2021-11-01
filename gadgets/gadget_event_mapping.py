
EVENT_MAPPING = [str('abd098_'), tuple[int(1), int(1)]]

class GadgetEventMapping():

    _event_mapping: [str, tuple[int, int]]

    def __init__(self, event_id: str, event_list: list[tuple[int, int]]):
        self._event_id = event_id
        self._characteristic_id, self._new_value = event_list
        self._event_mapping = EVENT_MAPPING

    def __del__(self):
        pass

    def get_event(self):
        for event in self._event_mapping:
            if self._event_id == event:
                
