import importlib.util
import pytest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock
from modules.base import BaseScanner
from colorama import Fore


def load_scanner(filename: str, mock_enumerator):
    spec = importlib.util.spec_from_file_location(
        filename.replace(".py", ""),
        Path(__file__).parent.parent / "modules" / filename,
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    spec.loader.exec_module(mod)
    cls = next(
        c for _, c in vars(mod).items()
        if isinstance(c, type) and issubclass(c, BaseScanner) and c is not BaseScanner
    )
    return cls(mock_enumerator)


SCANNER_FILES = [
    "01_certificate_transparency.py",
    "02_web_archives.py",
    "03_search_engines.py",
    "05_whoisxml.py",
    "07_github_search.py",
]


@pytest.mark.parametrize("filename", SCANNER_FILES)
def test_scanner_returns_set_on_timeout(filename, mock_enumerator):
    """Every scanner must return a set and not raise when all requests time out."""
    scanner = load_scanner(filename, mock_enumerator)
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.Timeout("simulated timeout")
    mock_enumerator.get_session.return_value = mock_session

    result = scanner.run()

    assert isinstance(result, set), f"{filename}: run() must return a set, got {type(result)}"


@pytest.mark.parametrize("filename", SCANNER_FILES)
def test_scanner_returns_set_on_connection_error(filename, mock_enumerator):
    """Every scanner must return a set and not raise on connection errors."""
    scanner = load_scanner(filename, mock_enumerator)
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.ConnectionError("simulated error")
    mock_enumerator.get_session.return_value = mock_session

    result = scanner.run()

    assert isinstance(result, set), f"{filename}: run() must return a set, got {type(result)}"
