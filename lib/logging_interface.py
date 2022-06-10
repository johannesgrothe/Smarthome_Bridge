import logging


class ILogging:
    _logger: logging.Logger

    def __init__(self):
        super().__init__()
        self._logger = self._get_logger()

    @classmethod
    def _get_logger(cls):
        return logging.getLogger(cls.__class__.__name__)