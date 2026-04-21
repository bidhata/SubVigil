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


def test_bruteforce_permutation_cap_default_wordlist(mock_enumerator):
    """With default wordlist and no custom wordlist, permutations must be capped at 500."""
    import importlib.util
    import concurrent.futures as cf
    import unittest.mock as um
    from pathlib import Path
    from modules.base import BaseScanner
    from colorama import Fore
    from tqdm import tqdm

    spec = importlib.util.spec_from_file_location(
        "08_dns_bruteforce",
        Path(__file__).parent.parent / "modules" / "08_dns_bruteforce.py",
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    mod.tqdm = tqdm
    spec.loader.exec_module(mod)

    scanner = mod.DnsBruteforce(mock_enumerator)
    # Use enough words to generate >500 permutations (each word × 27 variants ≈ 27 each)
    mock_enumerator.wordlist = None
    mock_enumerator.default_wordlist = [f"word{i}" for i in range(25)]  # 25 × 27 = 675 > 500

    submitted = []

    original_submit = cf.ThreadPoolExecutor.submit

    def spy_submit(self_exec, fn, *args, **kwargs):
        submitted.append(args[0] if args else None)
        future = cf.Future()
        future.set_result(None)
        return future

    with um.patch.object(cf.ThreadPoolExecutor, 'submit', spy_submit):
        try:
            scanner.run()
        except Exception:
            pass

    assert len(submitted) <= 500, (
        f"Default wordlist should produce at most 500 permutations, got {len(submitted)}"
    )
    assert len(submitted) == 500, (
        f"Cap should be exactly 500 when exceeded, got {len(submitted)}"
    )


def test_no_global_warnings_filterwarnings_in_subgrab():
    """subgrab.py must not use warnings.filterwarnings to suppress InsecureRequestWarning."""
    from pathlib import Path
    src = (Path(__file__).parent.parent / "subgrab.py").read_text(encoding='utf-8', errors='replace')
    assert "warnings.filterwarnings" not in src, (
        "Remove warnings.filterwarnings; use urllib3.disable_warnings() in get_session() instead"
    )


def test_module09_uses_resolver_not_socket(mock_enumerator):
    """module 09_reverse_dns must use dns PTR resolver, not socket.gethostbyaddr."""
    import importlib.util
    from pathlib import Path
    from unittest.mock import MagicMock
    from modules.base import BaseScanner

    mock_enumerator.resolve_domain.return_value = ["192.168.1.50"]
    mock_enumerator.domain = "example.com"
    mock_enumerator._is_valid_subdomain.return_value = True

    ptr_answer = MagicMock()
    ptr_answer.__str__ = lambda self: "found.example.com."
    mock_resolver = MagicMock()
    mock_resolver.resolve.return_value = [ptr_answer]
    mock_enumerator.get_resolver.return_value = mock_resolver

    mod_path = Path(__file__).parent.parent / "modules" / "09_reverse_dns.py"
    spec = importlib.util.spec_from_file_location("test_09_reverse_dns", mod_path)
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = MagicMock()
    spec.loader.exec_module(mod)

    scanner = mod.ReverseDNS(mock_enumerator)
    result = scanner.run()

    assert "found.example.com" in result, (
        "ReverseDNS.run() must return hostnames found via PTR lookups"
    )
    assert mock_resolver.resolve.called, (
        "get_resolver().resolve() must be called for PTR lookups"
    )
    # socket must not be imported in the module source
    src = mod_path.read_text()
    assert "import socket" not in src, (
        "Remove 'import socket'; use dns.reversename + get_resolver() instead"
    )


def test_virustotal_v3_api(mock_enumerator):
    """SecurityAPIs must use VT API v3 endpoint with x-apikey header, not v2."""
    import importlib.util
    from pathlib import Path
    from unittest.mock import MagicMock
    from modules.base import BaseScanner

    mock_enumerator.api_keys = {"virustotal": "test_key_123"}
    mock_enumerator.domain = "example.com"

    session_mock = MagicMock()
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {
        "data": [
            {"id": "api.example.com", "type": "domain"},
            {"id": "www.example.com", "type": "domain"},
        ],
        "meta": {}  # no cursor = single page, no more pages
    }
    session_mock.get.return_value = response_mock
    mock_enumerator.get_session.return_value = session_mock

    mod_path = Path(__file__).parent.parent / "modules" / "06_security_apis.py"
    spec = importlib.util.spec_from_file_location("test_06_security_apis", mod_path)
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = MagicMock()
    spec.loader.exec_module(mod)

    scanner = mod.SecurityAPIs(mock_enumerator)
    result = scanner.run()

    assert "api.example.com" in result, "VT v3 subdomains must be returned"
    assert "www.example.com" in result, "VT v3 subdomains must be returned"

    # Verify the v3 URL was used (not v2)
    call_args = session_mock.get.call_args_list[0]
    called_url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
    assert "v3" in called_url, (
        f"Must use VT API v3 URL, got: {called_url}"
    )
    assert "vtapi/v2" not in called_url, (
        "Must NOT use retired VT API v2 URL"
    )

    # Verify auth header not query param
    called_kwargs = call_args[1] if call_args[1] else {}
    headers = called_kwargs.get("headers", {})
    assert "x-apikey" in headers, (
        "VT v3 requires 'x-apikey' header, not query param"
    )
    assert headers["x-apikey"] == "test_key_123"
