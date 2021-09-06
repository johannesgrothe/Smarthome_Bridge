from system_info_tools import SystemInfoTools


def test_system_info_tools_git():
    version = SystemInfoTools.read_git_version()
    assert isinstance(version, str) or version is None


def test_system_info_tools_python():
    version = SystemInfoTools.read_python_version()
    assert isinstance(version, str) or version is None


def test_system_info_tools_pipenv():
    version = SystemInfoTools.read_pipenv_version()
    assert isinstance(version, str) or version is None


def test_system_info_tools_pio():
    version = SystemInfoTools.read_pio_version()
    assert isinstance(version, str) or version is None
