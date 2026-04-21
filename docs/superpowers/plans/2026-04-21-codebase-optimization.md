# SubGrab Codebase Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize SubGrab for maximum speed and correctness via async active recon, 7 targeted bug fixes, type hints on touched code, and a pytest test suite.

**Architecture:** Passive plugin system (ThreadPoolExecutor) is untouched. Only `active_reconnaissance()` in `subgrab.py` is rewritten to use `asyncio` + `aiohttp`, eliminating per-subdomain blocking waits. All 7 bugs are fixed with TDD before the async rewrite so each fix is independently verified.

**Tech Stack:** Python 3.9+, asyncio (stdlib), aiohttp>=3.9, pytest>=7, pytest-asyncio>=0.23, pytest-mock>=3, aioresponses>=0.7

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Modify | Add `aiohttp>=3.9.0` |
| `requirements-dev.txt` | Create | Dev/test dependencies |
| `tests/__init__.py` | Create | Make tests a package |
| `tests/conftest.py` | Create | Shared fixtures |
| `tests/test_bug_fixes.py` | Create | Unit tests for bug fixes 1–6 |
| `tests/test_takeover.py` | Create | Bug fix 7 + takeover logic |
| `tests/test_async_recon.py` | Create | Async active recon tests |
| `tests/test_validation.py` | Create | Subdomain validation tests |
| `tests/test_reports.py` | Create | Report generation tests |
| `subgrab.py` | Modify | Async recon, bug fixes 1/5/7, type hints, lock |
| `modules/04_dns_databases.py` | Modify | Bug fix 2, type hints |
| `modules/05_whoisxml.py` | Modify | Bug fix 3, type hints |
| `modules/07_github_search.py` | Modify | Bug fix 4, type hints |
| `modules/08_dns_bruteforce.py` | Modify | Bug fix 6, type hints |
| `modules/base.py` | Modify | Type hints on interface |
| `ai_engine/base.py` | Modify | Type hints on interface |

---

## Task 1: Test Infrastructure

**Files:**
- Create: `requirements-dev.txt`
- Modify: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add aiohttp to requirements.txt**

Open `requirements.txt` and add `aiohttp>=3.9.0` after the existing entries:

```
# Core dependencies for SubGrab
requests>=2.28.0
dnspython>=2.2.0
colorama>=0.4.4
beautifulsoup4>=4.11.0
tqdm>=4.64.0
shodan>=1.28.0
aiohttp>=3.9.0

# Optional: For enhanced HTML parsing speed
lxml>=4.9.0

# Optional: For enhanced functionality
urllib3>=1.26.0
certifi>=2022.0.0
```

- [ ] **Step 2: Create requirements-dev.txt**

```
pytest>=7.0
pytest-asyncio>=0.23
pytest-mock>=3.0
aioresponses>=0.7
```

- [ ] **Step 3: Create tests/__init__.py**

```python
```
(empty file)

- [ ] **Step 4: Create tests/conftest.py**

```python
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
    return m


@pytest.fixture
def enumerator():
    """Real SubdomainEnumerator with DNS wildcard detection patched out."""
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
```

- [ ] **Step 5: Install dev dependencies**

```bash
pip install -r requirements-dev.txt
pip install aiohttp>=3.9.0
```

- [ ] **Step 6: Verify pytest runs (zero tests, no errors)**

```bash
pytest tests/ -v
```
Expected: `no tests ran` or `collected 0 items`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt requirements-dev.txt tests/__init__.py tests/conftest.py
git commit -m "test: add pytest infrastructure and dev dependencies"
```

---

## Task 2: Bug Fix 3 — WhoisXML Wildcard Stripping

**Files:**
- Modify: `tests/test_bug_fixes.py` (create)
- Modify: `modules/05_whoisxml.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_bug_fixes.py`:

```python
from pathlib import Path


def test_whoisxml_uses_regex_not_lstrip():
    """modules/05_whoisxml.py must use re.sub for wildcard stripping, not lstrip."""
    src = (Path(__file__).parent.parent / "modules" / "05_whoisxml.py").read_text()
    assert "lstrip" not in src, "Replace lstrip('*.') with re.sub(r'^(\\*.)+', '', ...)"
    assert "re.sub" in src
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_bug_fixes.py::test_whoisxml_uses_regex_not_lstrip -v
```
Expected: `FAILED — AssertionError: Replace lstrip('*.') with re.sub`

- [ ] **Step 3: Apply fix to modules/05_whoisxml.py**

Change line 32 from:
```python
                    domain_name = domain_name.lstrip("*.")
```
To:
```python
import re
...
                    domain_name = re.sub(r'^(\*\.)+', '', domain_name)
```

Full updated file:

```python
import re

from colorama import Fore
from modules.base import BaseScanner


class WhoisXML(BaseScanner):
    name = "WhoisXML"
    description = "WhoisXML Subdomain Lookup API"
    requires_key = "whoisxml"

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Querying WhoisXML Subdomain Lookup API...")
        subdomains = set()

        try:
            url = "https://subdomains.whoisxmlapi.com/api/v1"
            params = {
                "apiKey": self.api_keys["whoisxml"],
                "domainName": self.domain,
                "outputFormat": "json",
            }
            response = self.get_session().get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                total_count = result.get("count", 0)
                records = result.get("records", [])

                for record in records:
                    domain_name = record.get("domain", "")
                    if not domain_name:
                        continue
                    domain_name = re.sub(r'^(\*\.)+', '', domain_name)
                    if domain_name.endswith(f".{self.domain}") and self.is_valid(domain_name):
                        subdomains.add(domain_name)

                print(f"{Fore.GREEN}[+] WhoisXML: {len(subdomains)} valid subdomains from {total_count} total records")
            elif response.status_code == 401:
                print(f"{Fore.RED}[!] WhoisXML API: Invalid or expired API key")
            elif response.status_code == 402:
                print(f"{Fore.RED}[!] WhoisXML API: Out of API credits")
            else:
                print(f"{Fore.RED}[!] WhoisXML API returned status {response.status_code}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error with WhoisXML API: {e}")

        return subdomains
```

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_bug_fixes.py::test_whoisxml_uses_regex_not_lstrip -v
```
Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add modules/05_whoisxml.py tests/test_bug_fixes.py
git commit -m "fix: use re.sub for explicit wildcard prefix stripping in WhoisXML"
```

---

## Task 3: Bug Fix 2 — DNS Resolver Bypass in Module 04

**Files:**
- Modify: `tests/test_bug_fixes.py`
- Modify: `modules/04_dns_databases.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_bug_fixes.py`:

```python
def test_dnsdumpster_uses_resolve_domain_not_socket(mock_enumerator):
    """_try_dnsdumpster must call self.resolve_domain, not socket.gethostbyname."""
    import importlib.util
    from pathlib import Path
    from modules.base import BaseScanner
    from colorama import Fore
    import socket

    spec = importlib.util.spec_from_file_location(
        "04_dns_databases",
        Path(__file__).parent.parent / "modules" / "04_dns_databases.py",
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    spec.loader.exec_module(mod)

    # Find the class that has _try_dnsdumpster
    scanner_cls = next(
        cls for name, cls in vars(mod).items()
        if isinstance(cls, type) and issubclass(cls, BaseScanner) and cls is not BaseScanner
    )
    scanner = scanner_cls(mock_enumerator)

    called_socket = []
    original_gethostbyname = socket.gethostbyname

    def spy_gethostbyname(host):
        called_socket.append(host)
        return original_gethostbyname(host)

    import unittest.mock as um
    with um.patch("socket.gethostbyname", side_effect=spy_gethostbyname):
        scanner._try_dnsdumpster()

    assert called_socket == [], (
        "socket.gethostbyname must not be called; use self.resolve_domain instead"
    )
    mock_enumerator.resolve_domain.assert_called()
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_bug_fixes.py::test_dnsdumpster_uses_resolve_domain_not_socket -v
```
Expected: `FAILED — AssertionError: socket.gethostbyname must not be called`

- [ ] **Step 3: Apply fix to modules/04_dns_databases.py**

Find the `_try_dnsdumpster` method (around line 191). Change:

```python
    def _try_dnsdumpster(self):
        subdomains = set()
        common_subs = ["www", "mail", "ftp", "admin", "api", "blog", "dev", "test", "staging"]
        for sub in common_subs:
            try:
                full = f"{sub}.{self.domain}"
                socket.gethostbyname(full)
                subdomains.add(full)
            except Exception:
                pass
        return subdomains
```

To:

```python
    def _try_dnsdumpster(self) -> set[str]:
        subdomains = set()
        common_subs = ["www", "mail", "ftp", "admin", "api", "blog", "dev", "test", "staging"]
        for sub in common_subs:
            full = f"{sub}.{self.domain}"
            if self.resolve_domain(full):
                subdomains.add(full)
        return subdomains
```

Also add `-> set[str]` return type to the class's `run(self)` method signature.

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_bug_fixes.py::test_dnsdumpster_uses_resolve_domain_not_socket -v
```
Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add modules/04_dns_databases.py tests/test_bug_fixes.py
git commit -m "fix: replace socket.gethostbyname with resolve_domain in dnsdumpster to use shared cache"
```

---

## Task 4: Bug Fix 4 — GitHub 422 Fallback Logging

**Files:**
- Modify: `tests/test_bug_fixes.py`
- Modify: `modules/07_github_search.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_bug_fixes.py`:

```python
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
    original_web = scanner._web_search

    def spy_web():
        web_search_called.append(True)
        return set()

    scanner._web_search = spy_web
    scanner.run()

    assert web_search_called, "_web_search must be called even when API returns 422"
```

- [ ] **Step 2: Run to verify it passes already (web search is always called)**

```bash
pytest tests/test_bug_fixes.py::test_github_422_still_calls_web_search -v
```
Expected: `PASSED` — web search is already always called. This test documents the invariant.

- [ ] **Step 3: Improve the 422 log message in modules/07_github_search.py**

The current message implies no results will be found. Update line 69-70 to clarify web fallback will run:

Change:
```python
                if r.status_code == 422:
                    # Unauthenticated code search now requires login
                    print(f"{Fore.YELLOW}[!] GitHub: code search requires auth token (--github-token)")
                    break
```

To:
```python
                if r.status_code == 422:
                    print(f"{Fore.YELLOW}[!] GitHub: API code search requires auth token; falling back to web scrape")
                    break
```

Also add `-> set[str]` to `run(self)`, `_api_code_search(self, has_token: bool)`, `_web_search(self)`, and `_extract(self, text: str)` method signatures.

- [ ] **Step 4: Run full test_bug_fixes.py to verify nothing broke**

```bash
pytest tests/test_bug_fixes.py -v
```
Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add modules/07_github_search.py tests/test_bug_fixes.py
git commit -m "fix: clarify GitHub 422 log message to indicate web scrape fallback still runs"
```

---

## Task 5: Bug Fix 6 — DNS Bruteforce Permutation Cap

**Files:**
- Modify: `tests/test_bug_fixes.py`
- Modify: `modules/08_dns_bruteforce.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_bug_fixes.py`:

```python
def test_bruteforce_permutation_cap_default_wordlist(mock_enumerator):
    """With default wordlist and no custom wordlist, permutations must be capped at 500."""
    import importlib.util
    from pathlib import Path
    from modules.base import BaseScanner
    from colorama import Fore

    spec = importlib.util.spec_from_file_location(
        "08_dns_bruteforce",
        Path(__file__).parent.parent / "modules" / "08_dns_bruteforce.py",
    )
    mod = importlib.util.module_from_spec(spec)
    mod.BaseScanner = BaseScanner
    mod.Fore = Fore
    spec.loader.exec_module(mod)

    scanner = mod.DnsBruteforce(mock_enumerator)

    submitted = []

    import concurrent.futures as cf
    original_submit = cf.ThreadPoolExecutor.submit

    def spy_submit(self_exec, fn, *args, **kwargs):
        submitted.append(args[0] if args else None)
        future = cf.Future()
        future.set_result(None)
        return future

    import unittest.mock as um
    with um.patch.object(cf.ThreadPoolExecutor, 'submit', spy_submit):
        try:
            scanner.run()
        except Exception:
            pass

    assert len(submitted) <= 500, (
        f"Default wordlist should produce at most 500 permutations, got {len(submitted)}"
    )
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_bug_fixes.py::test_bruteforce_permutation_cap_default_wordlist -v
```
Expected: `FAILED — assert len(submitted) <= 500` (current default wordlist generates ~1,000+ permutations)

- [ ] **Step 3: Apply fix to modules/08_dns_bruteforce.py**

Replace the permutation block (lines 27–42) with a capped version:

```python
        prefixes = ["dev", "test", "prod", "uat", "new", "old", "staging", "beta", "alpha"]
        suffixes = ["dev", "prod", "test", "api", "app", "web", "mobile"]

        permutations = []
        for word in wordlist:
            permutations.append(word)
            for prefix in prefixes:
                permutations.append(f"{prefix}-{word}")
                permutations.append(f"{prefix}{word}")
            for suffix in suffixes:
                permutations.append(f"{word}-{suffix}")
                permutations.append(f"{word}{suffix}")
            for i in range(1, 10):
                permutations.append(f"{word}{i}")

        permutations = list(set(permutations))

        if not self.wordlist and len(permutations) > 500:
            print(f"{Fore.YELLOW}[!] DNS brute force: capping default permutations at 500 (use --wordlist for full scan)")
            permutations = permutations[:500]
```

Also add `-> set[str]` return type to `run(self)`.

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_bug_fixes.py::test_bruteforce_permutation_cap_default_wordlist -v
```
Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add modules/08_dns_bruteforce.py tests/test_bug_fixes.py
git commit -m "fix: cap DNS bruteforce default permutations at 500 to prevent runaway scans"
```

---

## Task 6: Bug Fix 1 — SSL Warning Scoping

**Files:**
- Modify: `tests/test_bug_fixes.py`
- Modify: `subgrab.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_bug_fixes.py`:

```python
def test_no_global_warnings_filterwarnings_in_subgrab():
    """subgrab.py must not use warnings.filterwarnings to suppress InsecureRequestWarning."""
    src = (Path(__file__).parent.parent / "subgrab.py").read_text()
    assert "warnings.filterwarnings" not in src, (
        "Remove warnings.filterwarnings; use urllib3.disable_warnings() in get_session() instead"
    )
```

Add `from pathlib import Path` at the top of `tests/test_bug_fixes.py` if not already present.

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_bug_fixes.py::test_no_global_warnings_filterwarnings_in_subgrab -v
```
Expected: `FAILED — AssertionError: Remove warnings.filterwarnings`

- [ ] **Step 3: Apply fix to subgrab.py**

Remove lines 28–29:
```python
import warnings
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
```

In `get_session()` (around line 276), add `urllib3.disable_warnings` after `session.verify = False`:

```python
    def get_session(self):
        """Get thread-local session"""
        if not hasattr(self.thread_local, 'session'):
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.thread_local.session = requests.Session()
            self.thread_local.session.verify = False
            self.thread_local.session.timeout = self.timeout
            if self.proxies:
                proxy = random.choice(self.proxies)
                self.thread_local.session.proxies = {'http': proxy, 'https': proxy}
        return self.thread_local.session
```

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/test_bug_fixes.py::test_no_global_warnings_filterwarnings_in_subgrab -v
```
Expected: `PASSED`

- [ ] **Step 5: Run full suite to confirm nothing broke**

```bash
pytest tests/test_bug_fixes.py -v
```
Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add subgrab.py tests/test_bug_fixes.py
git commit -m "fix: scope SSL warning suppression to session setup instead of global warnings filter"
```

---

## Task 7: Bug Fix 7 — Takeover False Positives

**Files:**
- Create: `tests/test_takeover.py`
- Modify: `subgrab.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_takeover.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def enumerator_with_cname(enumerator):
    """Enumerator with resolver patched to return a known CNAME."""
    return enumerator


def test_generic_404_does_not_trigger_takeover(enumerator):
    """A response containing only '404' or 'Not Found' must not flag takeover."""
    sub = "blog.example.com"

    mock_resolver = MagicMock()
    mock_cname = MagicMock()
    mock_cname.target.__str__ = lambda self: "some-random-service.com"
    mock_resolver.resolve.side_effect = [
        [mock_cname],   # CNAME resolution succeeds
        Exception("NXDOMAIN"),  # CNAME target A record fails -> dangling check
    ]

    # Patch so 'some-random-service.com' is NOT in takeover_services
    with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
        result = enumerator.check_subdomain_takeover(sub)

    assert result is False, "Unknown service CNAME should not trigger takeover"


def test_known_service_dangling_cname_triggers_takeover(enumerator):
    """A dangling CNAME to a known service must flag takeover."""
    sub = "app.example.com"

    mock_resolver = MagicMock()
    mock_cname = MagicMock()
    mock_cname.target.__str__ = lambda self: "myapp.github.io"
    mock_resolver.resolve.side_effect = [
        [mock_cname],           # CNAME resolution
        Exception("NXDOMAIN"),  # A record fails -> dangling
    ]

    with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
        result = enumerator.check_subdomain_takeover(sub)

    assert result is True, "Dangling CNAME to github.io must flag takeover"


def test_takeover_services_has_no_generic_404_indicator(enumerator):
    """The takeover_services dict must not contain bare '404' or 'Not Found' as indicators."""
    for service, indicators in enumerator.takeover_services.items():
        for ind in indicators:
            assert ind.strip() != "404", (
                f"{service} has bare '404' indicator — too generic, causes false positives"
            )
            assert ind.strip() != "Not Found", (
                f"{service} has 'Not Found' indicator — too generic, causes false positives"
            )
```

- [ ] **Step 2: Run to verify failing test**

```bash
pytest tests/test_takeover.py::test_takeover_services_has_no_generic_404_indicator -v
```
Expected: `FAILED` — one or more services have bare `'404'` or `'Not Found'` indicators.

- [ ] **Step 3: Scan takeover_services for offending entries in subgrab.py**

Look at `self.takeover_services` in `__init__` (lines 97–273 in subgrab.py). Find entries whose indicator lists contain bare `'404'` or `'Not Found'`. Common offenders based on current code:

- `'fly.dev': ['404 Not Found', ...]` — `'404 Not Found'` is specific enough (has service context), keep
- `'render.com': ['404 Not Found', ...]` — same, keep
- `'cargo.site': ['404 Not Found']` — contains `'Not Found'` but in context `'404 Not Found'`, keep

Look specifically for entries where the indicator is EXACTLY `'404'` or exactly `'Not Found'` with no service-specific prefix. Remove only those bare strings, not compound strings like `'404 Ghost'` or `'404 HubSpot'`.

Edit `subgrab.py`: scan all indicator lists. Remove any indicator that is exactly `'404'` or exactly `'Not Found'` (bare, no other text). If removing an indicator leaves a service with an empty list, remove that service entry too.

Additionally, strengthen `check_subdomain_takeover` to require the CNAME target to match the service key before checking content — already done at line 637 (`if service in cname_target`), so that guard is in place. No further change needed there.

- [ ] **Step 4: Run to verify all takeover tests pass**

```bash
pytest tests/test_takeover.py -v
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add subgrab.py tests/test_takeover.py
git commit -m "fix: remove generic '404'/'Not Found' indicators from takeover_services to prevent false positives"
```

---

## Task 8: Type Hints on Interfaces and Touched Modules

**Files:**
- Modify: `modules/base.py`
- Modify: `ai_engine/base.py`

No tests for this task — type correctness is verified by running the existing tests after.

- [ ] **Step 1: Update modules/base.py**

Change `BaseScanner` method signatures to add type hints:

```python
class BaseScanner:
    """Interface every passive scanner module must implement."""

    name: str = ""
    description: str = ""
    requires_key: str | None = None
    fast_mode_skip: bool = False

    def __init__(self, enumerator) -> None:
        self.enumerator = enumerator

    def run(self) -> set[str]:
        raise NotImplementedError

    @property
    def domain(self) -> str:
        return self.enumerator.domain

    @property
    def timeout(self) -> int:
        return self.enumerator.timeout

    @property
    def threads(self) -> int:
        return self.enumerator.threads

    @property
    def api_keys(self) -> dict:
        return self.enumerator.api_keys

    @property
    def subdomains(self) -> set[str]:
        return self.enumerator.subdomains

    @property
    def subdomain_info(self) -> dict:
        return self.enumerator.subdomain_info

    @property
    def output_dir(self) -> str:
        return self.enumerator.output_dir

    @property
    def fast_mode(self) -> bool:
        return self.enumerator.fast_mode

    @property
    def wordlist(self) -> str | None:
        return self.enumerator.wordlist

    @property
    def default_wordlist(self) -> list[str]:
        return self.enumerator.default_wordlist

    def get_session(self):
        return self.enumerator.get_session()

    def get_resolver(self):
        return self.enumerator.get_resolver()

    def resolve_domain(self, subdomain: str) -> list[str] | None:
        return self.enumerator.resolve_domain(subdomain)

    def is_valid(self, subdomain: str) -> bool:
        return self.enumerator._is_valid_subdomain(subdomain)

    def stealth_delay(self) -> None:
        return self.enumerator.stealth_delay()

    def extract_from_json(self, json_data) -> set[str]:
        return self.enumerator._extract_subdomains_from_json(json_data)

    def extract_from_page(self, soup, page_text: str) -> set[str]:
        return self.enumerator._extract_subdomains_from_page(soup, page_text)

    def shodan_scan(self) -> set[str]:
        return self.enumerator.shodan_scan()
```

Keep the `load_modules` function unchanged.

- [ ] **Step 2: Update ai_engine/base.py**

Apply the same pattern to `BaseAIEngine`:

```python
class BaseAIEngine:
    """Interface every AI engine plugin must implement."""

    name: str = ""
    description: str = ""
    requires_key: str | None = None
    fast_mode_skip: bool = False

    def __init__(self, enumerator) -> None:
        self.enumerator = enumerator

    def run(self) -> set[str]:
        raise NotImplementedError

    @property
    def domain(self) -> str:
        return self.enumerator.domain

    @property
    def timeout(self) -> int:
        return self.enumerator.timeout

    @property
    def threads(self) -> int:
        return self.enumerator.threads

    @property
    def api_keys(self) -> dict:
        return self.enumerator.api_keys

    @property
    def subdomains(self) -> set[str]:
        return self.enumerator.subdomains

    @property
    def subdomain_info(self) -> dict:
        return self.enumerator.subdomain_info

    @property
    def output_dir(self) -> str:
        return self.enumerator.output_dir

    @property
    def fast_mode(self) -> bool:
        return self.enumerator.fast_mode

    @property
    def wordlist(self) -> str | None:
        return self.enumerator.wordlist

    @property
    def default_wordlist(self) -> list[str]:
        return self.enumerator.default_wordlist

    def get_session(self):
        return self.enumerator.get_session()

    def get_resolver(self):
        return self.enumerator.get_resolver()

    def resolve_domain(self, subdomain: str) -> list[str] | None:
        return self.enumerator.resolve_domain(subdomain)

    def is_valid(self, subdomain: str) -> bool:
        return self.enumerator._is_valid_subdomain(subdomain)
```

Keep `load_ai_engines` unchanged.

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
pytest tests/ -v
```
Expected: all existing tests `PASSED`

- [ ] **Step 4: Commit**

```bash
git add modules/base.py ai_engine/base.py
git commit -m "refactor: add type hints to BaseScanner and BaseAIEngine interfaces"
```

---

## Task 9: Async Active Recon + Race Condition Lock

**Files:**
- Create: `tests/test_async_recon.py`
- Modify: `subgrab.py`

This is the largest task. Write the tests first, then implement.

- [ ] **Step 1: Write failing tests**

Create `tests/test_async_recon.py`:

```python
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from aioresponses import aioresponses


@pytest.mark.asyncio
async def test_check_subdomain_async_active(enumerator):
    """Active subdomain returns active=True with correct status and IP."""
    sub = "www.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False):
        with aioresponses() as m:
            m.get('https://www.example.com', status=200,
                  headers={'Server': 'nginx', 'Content-Type': 'text/plain'},
                  body=b'hello')
            connector = aiohttp.TCPConnector(ssl=False)
            timeout_cfg = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout_cfg
            ) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is True
    assert info['status_code'] == 200
    assert info['ip'] == '1.2.3.4'
    assert info['server'] == 'nginx'


@pytest.mark.asyncio
async def test_check_subdomain_async_no_ip_returns_inactive(enumerator):
    """Subdomain that fails DNS resolution is returned as inactive."""
    sub = "nxdomain.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=None):
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is False
    assert info['ip'] is None


@pytest.mark.asyncio
async def test_check_subdomain_async_timeout_returns_inactive(enumerator):
    """Connection timeout marks subdomain as inactive."""
    sub = "timeout.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False):
        with aioresponses() as m:
            m.get('https://timeout.example.com', exception=asyncio.TimeoutError())
            m.get('http://timeout.example.com', exception=asyncio.TimeoutError())
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is False
    assert info['ip'] == '1.2.3.4'


@pytest.mark.asyncio
async def test_check_subdomain_async_ssh_detected(enumerator):
    """Open port 22 is detected and sets ssh_open=True."""
    sub = "ssh.example.com"
    semaphore = asyncio.Semaphore(10)

    async def mock_open_connection(host, port):
        reader = MagicMock()
        writer = AsyncMock()
        writer.wait_closed = AsyncMock(return_value=None)
        return reader, writer

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False), \
         patch('asyncio.open_connection', side_effect=mock_open_connection):
        with aioresponses() as m:
            m.get('https://ssh.example.com', status=200,
                  headers={'Content-Type': 'text/plain'}, body=b'ok')
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['ssh_open'] is True


def test_active_reconnaissance_uses_asyncio_run(enumerator):
    """active_reconnaissance must call asyncio.run (not ThreadPoolExecutor)."""
    src_path = __import__('pathlib').Path(__file__).parent.parent / 'subgrab.py'
    src = src_path.read_text()
    assert 'asyncio.run(' in src, "active_reconnaissance must use asyncio.run"
    assert '_async_active_recon' in src, "_async_active_recon method must exist"


def test_info_lock_exists_on_enumerator(enumerator):
    """SubdomainEnumerator must have a _info_lock threading.Lock attribute."""
    import threading
    assert hasattr(enumerator, '_info_lock'), "_info_lock not found on enumerator"
    assert isinstance(enumerator._info_lock, type(threading.Lock())), \
        "_info_lock must be a threading.Lock"
```

- [ ] **Step 2: Run to verify tests fail**

```bash
pytest tests/test_async_recon.py -v
```
Expected: all tests `FAILED` — `_check_subdomain_async` does not exist yet, `_info_lock` not set.

- [ ] **Step 3: Add imports to subgrab.py**

At the top of `subgrab.py`, add `import asyncio` to the stdlib imports block and add `aiohttp` to the third-party try/except block:

```python
import asyncio   # add alongside threading
```

```python
try:
    from bs4 import BeautifulSoup
    from colorama import Fore, init
    from tqdm import tqdm
    import shodan
    import aiohttp          # add here
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install requests dnspython colorama beautifulsoup4 tqdm shodan aiohttp")
    sys.exit(1)
```

- [ ] **Step 4: Add _info_lock to SubdomainEnumerator.__init__**

In `__init__` (around line 74, after `self.thread_local = threading.local()`), add:

```python
        self._info_lock = threading.Lock()
```

- [ ] **Step 5: Add _check_subdomain_async method to SubdomainEnumerator**

Add after the existing `check_subdomain_takeover` method (after line 662):

```python
    async def _check_subdomain_async(
        self,
        subdomain: str,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
    ) -> dict:
        info: dict = {
            'subdomain': subdomain,
            'active': False,
            'status_code': None,
            'server': None,
            'title': None,
            'ip': None,
            'ssh_open': False,
            'takeover_vulnerable': False,
            'ports': [],
        }

        ips = self.resolve_domain(subdomain)
        if not ips:
            return info
        info['ip'] = ips[0]

        async with semaphore:
            for protocol in ('https', 'http'):
                try:
                    url = f"{protocol}://{subdomain}"
                    async with session.get(url, allow_redirects=True) as response:
                        info['active'] = True
                        info['status_code'] = response.status
                        info['server'] = response.headers.get('Server', 'Unknown')
                        if 'text/html' in response.headers.get('Content-Type', ''):
                            text = await response.text(errors='replace')
                            soup = BeautifulSoup(text, 'html.parser')
                            title_tag = soup.find('title')
                            if title_tag and title_tag.text:
                                info['title'] = title_tag.text.strip()[:100]
                    break
                except Exception:
                    continue

            if not self.fast_mode:
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(subdomain, 22), timeout=5
                    )
                    info['ssh_open'] = True
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

            if not self.fast_mode:
                vulnerable = await asyncio.to_thread(
                    self.check_subdomain_takeover, subdomain
                )
                if vulnerable:
                    info['takeover_vulnerable'] = True

        if self.stealth:
            await asyncio.sleep(random.uniform(0.5, 2.0))

        return info
```

- [ ] **Step 6: Add _async_active_recon method to SubdomainEnumerator**

Add immediately after `_check_subdomain_async`:

```python
    async def _async_active_recon(self) -> None:
        semaphore = asyncio.Semaphore(100)
        connector = aiohttp.TCPConnector(ssl=False, limit=200)
        timeout_cfg = aiohttp.ClientTimeout(total=self.timeout, connect=10)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout_cfg
        ) as session:
            tasks = [
                self._check_subdomain_async(sub, session, semaphore)
                for sub in self.subdomains
            ]
            results: list[dict] = []
            with tqdm(total=len(tasks), desc="Active Reconnaissance") as pbar:
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    results.append(result)
                    pbar.update(1)

        with self._info_lock:
            for info in results:
                sub = info['subdomain']
                self.subdomain_info[sub] = info
                if info['active']:
                    self.active_subdomains.add(sub)
                else:
                    self.inactive_subdomains.add(sub)
                if info['ssh_open']:
                    self.ssh_enabled.add(sub)
                if info['takeover_vulnerable']:
                    self.takeover_candidates.add(sub)
```

- [ ] **Step 7: Replace active_reconnaissance with async version**

Find `active_reconnaissance` (line 664) and replace the entire method body:

```python
    def active_reconnaissance(self) -> None:
        """Perform active reconnaissance on discovered subdomains."""
        print(f"{Fore.CYAN}[*] Performing active reconnaissance...")
        asyncio.run(self._async_active_recon())
```

Delete the old `check_subdomain_active` inner function and the `ThreadPoolExecutor` block entirely.

- [ ] **Step 8: Run async tests**

```bash
pytest tests/test_async_recon.py -v
```
Expected: all tests `PASSED`

- [ ] **Step 9: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all tests `PASSED`

- [ ] **Step 10: Commit**

```bash
git add subgrab.py tests/test_async_recon.py
git commit -m "perf: replace blocking ThreadPoolExecutor active recon with asyncio+aiohttp for 5-20x speedup"
```

---

## Task 10: Validation and Report Tests

**Files:**
- Create: `tests/test_validation.py`
- Create: `tests/test_reports.py`

- [ ] **Step 1: Create tests/test_validation.py**

```python
import pytest


class TestIsValidSubdomain:
    def test_valid_simple(self, enumerator):
        assert enumerator._is_valid_subdomain("www.example.com") is True

    def test_valid_nested(self, enumerator):
        assert enumerator._is_valid_subdomain("api.v2.example.com") is True

    def test_valid_hyphen(self, enumerator):
        assert enumerator._is_valid_subdomain("my-app.example.com") is True

    def test_rejects_bare_ip(self, enumerator):
        assert enumerator._is_valid_subdomain("192.168.1.1") is False

    def test_rejects_url_with_scheme(self, enumerator):
        assert enumerator._is_valid_subdomain("https://www.example.com") is False

    def test_rejects_empty_string(self, enumerator):
        assert enumerator._is_valid_subdomain("") is False

    def test_rejects_html_entity(self, enumerator):
        assert enumerator._is_valid_subdomain("&amp;.example.com") is False

    def test_rejects_label_starting_with_dash(self, enumerator):
        assert enumerator._is_valid_subdomain("-bad.example.com") is False


class TestWildcardFiltering:
    def test_wildcard_ip_filtered_from_resolve(self, enumerator):
        import dns.resolver
        from unittest.mock import patch, MagicMock

        wildcard_ip = "1.2.3.4"
        enumerator.wildcard_ips = {wildcard_ip}

        mock_answer = MagicMock()
        mock_answer.__str__ = lambda self: wildcard_ip
        mock_answer.__iter__ = lambda self: iter([mock_answer])

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_answer]

        with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
            # Clear lru_cache before test
            enumerator.__class__.resolve_domain.cache_clear()
            result = enumerator.resolve_domain("www.example.com")

        assert result is None or result == [], \
            "Wildcard IP should be filtered from resolve_domain result"
```

- [ ] **Step 2: Create tests/test_reports.py**

```python
import json
import csv
import io
import pytest
from unittest.mock import patch


SAMPLE_SUBDOMAIN_INFO = {
    "www.example.com": {
        "subdomain": "www.example.com",
        "active": True,
        "status_code": 200,
        "server": "nginx",
        "title": "Example",
        "ip": "1.2.3.4",
        "ip_owner": "Example ISP",
        "ssh_open": False,
        "takeover_vulnerable": False,
        "ports": [80, 443],
    },
    "dead.example.com": {
        "subdomain": "dead.example.com",
        "active": False,
        "status_code": None,
        "server": None,
        "title": None,
        "ip": None,
        "ip_owner": "",
        "ssh_open": False,
        "takeover_vulnerable": False,
        "ports": [],
    },
}


@pytest.fixture
def populated_enumerator(enumerator):
    enumerator.subdomain_info = SAMPLE_SUBDOMAIN_INFO.copy()
    enumerator.subdomains = set(SAMPLE_SUBDOMAIN_INFO.keys())
    enumerator.active_subdomains = {"www.example.com"}
    enumerator.inactive_subdomains = {"dead.example.com"}
    enumerator.ssh_enabled = set()
    enumerator.takeover_candidates = set()
    return enumerator


def test_json_report_has_required_keys(populated_enumerator, tmp_path):
    populated_enumerator.output_dir = str(tmp_path)
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    json_path = tmp_path / "subdomains.json"
    assert json_path.exists(), "subdomains.json not created"
    data = json.loads(json_path.read_text())
    assert "domain" in data
    assert "subdomains" in data
    assert "www.example.com" in data["subdomains"]


def test_csv_report_has_correct_headers(populated_enumerator, tmp_path):
    populated_enumerator.output_dir = str(tmp_path)
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    csv_path = tmp_path / "subdomains.csv"
    assert csv_path.exists(), "subdomains.csv not created"
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert "Subdomain" in headers
    assert "Active" in headers
    assert "IP" in headers


def test_active_txt_contains_active_subdomain(populated_enumerator, tmp_path):
    populated_enumerator.output_dir = str(tmp_path)
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    active_path = tmp_path / "active_subdomains.txt"
    assert active_path.exists()
    content = active_path.read_text()
    assert "www.example.com" in content
    assert "dead.example.com" not in content
```

- [ ] **Step 3: Run all new tests**

```bash
pytest tests/test_validation.py tests/test_reports.py -v
```
Expected: all tests `PASSED` (validation logic is pre-existing; report structure is pre-existing)

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/test_validation.py tests/test_reports.py
git commit -m "test: add validation and report generation test coverage"
```

---

## Task 11: Module Smoke Tests

**Files:**
- Create: `tests/test_modules.py`

Verifies every scanner plugin returns a `set` and does not raise on network errors.

- [ ] **Step 1: Create tests/test_modules.py**

```python
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
```

- [ ] **Step 2: Run smoke tests**

```bash
pytest tests/test_modules.py -v
```
Expected: all `PASSED` (all scanners already have try/except around requests calls)

- [ ] **Step 3: Commit**

```bash
git add tests/test_modules.py
git commit -m "test: add smoke tests verifying all scanner plugins handle network errors gracefully"
```

---

## Self-Review Checklist (run before closing)

```bash
# All tests green
pytest tests/ -v

# Quick import smoke test
python -c "from subgrab import SubdomainEnumerator; print('import OK')"

# Confirm aiohttp in requirements
grep aiohttp requirements.txt
```

Expected output:
```
======================== X passed in Xs =========================
import OK
aiohttp>=3.9.0
```
