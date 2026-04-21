from pathlib import Path


def test_whoisxml_uses_regex_not_lstrip():
    """modules/05_whoisxml.py must use re.sub for wildcard stripping, not lstrip."""
    src = (Path(__file__).parent.parent / "modules" / "05_whoisxml.py").read_text()
    assert "lstrip" not in src, "Replace lstrip('*.') with re.sub(r'^(\\*.)+', '', ...)"
    assert "re.sub" in src


def test_dnsdumpster_uses_resolve_domain_not_socket(mock_enumerator):
    """_try_dnsdumpster must call self.resolve_domain, not socket.gethostbyname."""
    import importlib.util
    import socket
    import unittest.mock as um
    from pathlib import Path
    from modules.base import BaseScanner
    from colorama import Fore

    spec = importlib.util.spec_from_file_location(
        "04_dns_databases",
        Path(__file__).parent.parent / "modules" / "04_dns_databases.py",
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    spec.loader.exec_module(mod)

    scanner_cls = next(
        cls for name, cls in vars(mod).items()
        if isinstance(cls, type) and issubclass(cls, BaseScanner) and cls is not BaseScanner
    )
    scanner = scanner_cls(mock_enumerator)

    called_socket = []
    original = socket.gethostbyname

    def spy(host):
        called_socket.append(host)
        return original(host)

    with um.patch("socket.gethostbyname", side_effect=spy):
        scanner._try_dnsdumpster()

    assert called_socket == [], (
        "socket.gethostbyname must not be called; use self.resolve_domain instead"
    )
    mock_enumerator.resolve_domain.assert_called()


def test_github_422_still_calls_web_search(mock_enumerator, mocker):
    """When API returns 422, _web_search must still be called."""
    import importlib.util
    from pathlib import Path
    from modules.base import BaseScanner
    from colorama import Fore

    spec = importlib.util.spec_from_file_location(
        "07_github_search",
        Path(__file__).parent.parent / "modules" / "07_github_search.py",
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    spec.loader.exec_module(mod)

    scanner = mod.GitHubSearch(mock_enumerator)

    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 422
    mock_resp.json.return_value = {}
    mock_enumerator.get_session.return_value.get.return_value = mock_resp

    web_search_called = []
    def spy_web():
        web_search_called.append(True)
        return set()

    scanner._web_search = spy_web
    scanner.run()

    assert web_search_called, "_web_search must be called even when API returns 422"
