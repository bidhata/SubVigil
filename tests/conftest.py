import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_enumerator():
    """Minimal mock enumerator for plugin unit tests."""
    m = MagicMock()
    m.domain = "example.com"
    m.api_keys = {}
    m.subdomains = set()
    m.subdomain_info = {}
    m.output_dir = "/tmp/test_subgrab"
    m.fast_mode = False
    m.threads = 5
    m.timeout = 10
    m.wordlist = None
    m.default_wordlist = ["www", "mail", "api", "dev", "test"]
    m.wildcard_ips = set()
    m.resolve_domain.return_value = ["1.2.3.4"]
    m._is_valid_subdomain.return_value = True
    m.stealth = False
    m.proxies = []
    m.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
    m.get_session.return_value = MagicMock()
    m.get_resolver.return_value = MagicMock()
    m.stealth_delay.return_value = None
    m.shodan_scan.return_value = set()
    m._extract_subdomains_from_json.return_value = set()
    m._extract_subdomains_from_page.return_value = set()
    return m


@pytest.fixture
def enumerator(tmp_path, monkeypatch):
    """Real SubdomainEnumerator with DNS wildcard detection patched out."""
    monkeypatch.chdir(tmp_path)
    from subgrab import SubdomainEnumerator
    with patch.object(SubdomainEnumerator, '_detect_wildcards'):
        e = SubdomainEnumerator("example.com", threads=5, timeout=10)
    return e


@pytest.fixture(autouse=True)
def clear_resolve_cache():
    """Clear the lru_cache on resolve_domain between tests."""
    yield
    try:
        from subgrab import SubdomainEnumerator
        SubdomainEnumerator.resolve_domain.cache_clear()
    except AttributeError:
        pass
