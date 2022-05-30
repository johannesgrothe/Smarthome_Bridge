class GadgetUpdateContainer:
    _source_id: str
    name: bool

    def __init__(self, origin_id: str):
        self._source_id = origin_id
        self.name = False

    @property
    def origin(self) -> str:
        return self._source_id
