"""Module to contain all Exceptions used by multiple Toolkit Classes"""


class ToolkitException(Exception):
    def __init__(self):
        super().__init__("ToolkitException")
