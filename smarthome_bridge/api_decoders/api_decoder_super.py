from abc import ABCMeta

from lib.logging_interface import ILogging


class ApiDecoderSuper(ILogging, metaclass=ABCMeta):
    pass
