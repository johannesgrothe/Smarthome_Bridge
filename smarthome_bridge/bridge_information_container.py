from datetime import datetime


class BridgeInformationContainer:

    name: str
    git_branch: str
    git_commit: str
    running_since: datetime

    pio_version: str
    pipenv_version: str
    git_version: str
    python_version: str

    def __init__(self, name: str, git_branch: str, git_commit: str, running_since: datetime, pio_version: str,
                 pipenv_version: str, git_version: str, python_version: str):
        self.name = name
        self.git_branch = git_branch
        self.git_commit = git_commit
        self.running_since = running_since

        self.pio_version = pio_version
        self.pipenv_version = pipenv_version
        self.git_version = git_version
        self.python_version = python_version
