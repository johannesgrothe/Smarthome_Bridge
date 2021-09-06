from datetime import datetime
from typing import Optional


class BridgeInformationContainer:

    name: str
    git_branch: Optional[str]
    git_commit: Optional[str]
    running_since: datetime

    pio_version: Optional[str]
    pipenv_version: Optional[str]
    git_version: Optional[str]
    python_version: Optional[str]

    def __init__(self, name: str, git_branch: Optional[str], git_commit: Optional[str], running_since: datetime,
                 pio_version: Optional[str], pipenv_version: Optional[str], git_version: Optional[str],
                 python_version: Optional[str]):
        self.name = name
        self.git_branch = git_branch
        self.git_commit = git_commit
        self.running_since = running_since

        self.pio_version = pio_version
        self.pipenv_version = pipenv_version
        self.git_version = git_version
        self.python_version = python_version
