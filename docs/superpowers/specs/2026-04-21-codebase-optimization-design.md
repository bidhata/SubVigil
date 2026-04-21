# SubGrab Codebase Optimization Design

**Date:** 2026-04-21
**Scope:** `subgrab.py` + `modules/04`, `05`, `07`, `08` + `modules/base.py` + `ai_engine/base.py`
**Out of scope:** `subgrab_gui.py`, plugin API contracts, CLI interface, report formats

---

## Goal

Full optimization pass: async active recon for maximum speed, seven targeted bug fixes for correctness, type hints on touched code, and a pytest suite covering all changes.

---

## Architecture

### What stays the same

- All 9 passive scanner plugins (`modules/`) — no API changes
- Both AI engines (`ai_engine/`) — no changes
- `BaseScanner` / `BaseAIEngine` interfaces — no breaking changes
- `subgrab_gui.py` — untouched
- CLI argument interface — no changes
- All report formats (TXT, JSON, CSV, HTML)

### Active recon — before vs. after

**Before (blocking):**
```
active_recon()
  └── ThreadPoolExecutor → _check_subdomain(sub)
        ├── requests.get(HTTPS) — blocks up to 10s
        ├── requests.get(HTTP)  — blocks up to 10s
        └── socket.connect_ex(22) — blocks up to 5s
        Total: up to 25s per subdomain, limited by thread count
```

**After (async):**
```
active_recon()
  └── asyncio.run(_async_active_recon())
        └── asyncio.gather(*[_check_subdomain_async(sub) for sub in subdomains])
              ├── aiohttp.get(HTTPS) — non-blocking
              ├── aiohttp.get(HTTP)  — non-blocking
              └── asyncio.open_connection(22) — non-blocking
              Total: all subdomains checked concurrently, bounded by semaphore(100)
```

`asyncio.Semaphore(100)` caps concurrent connections — tunable, avoids OS fd limit exhaustion and target overload. `shodan_active_ip_scan()` and all passive plugins remain synchronous — they are not the bottleneck.

**New dependency:** `aiohttp>=3.9.0`

---

## Bug Fixes

### 1. SSL warning suppression removed (`subgrab.py:29`)
Remove `warnings.filterwarnings("ignore")`. Use `urllib3.disable_warnings()` scoped to the requests session only, not globally. SSL verification stays disabled for scanning (intentional).

### 2. DNS resolver bypass in module 04 (`modules/04_dns_databases.py:197`)
Replace `socket.gethostbyaddr(full)` with `self.resolve_domain(full)` — uses the shared thread-local resolver and `lru_cache`.

### 3. WhoisXML double-wildcard strip (`modules/05_whoisxml.py:32`)
Replace `domain_name.lstrip("*.")` with `re.sub(r'^(\*\.)+', '', domain_name)` — strips all leading `*.` segments, not just one.

### 4. GitHub 422 stops all queries (`modules/07_github_search.py:68`)
On 422, fall back to unauthenticated web scraping immediately instead of `break`-ing the entire query loop.

### 5. Race condition in `subdomain_info` updates
Add `threading.Lock` to `SubdomainEnumerator.__init__()`. All writes to `subdomain_info`, `active_subdomains`, `ssh_enabled`, `takeover_candidates`, `inactive_subdomains` acquire the lock. Reads remain lock-free.

### 6. DNS bruteforce permutation explosion (`modules/08_dns_bruteforce.py`)
Cap permutation candidates at 500 when no custom wordlist is provided. Log a message if the cap is hit. Large custom wordlists are unaffected.

### 7. Takeover false positives (`subgrab.py`)
Remove generic indicators `'404'` and `'Not Found'` from `takeover_services`. Verify CNAME target points to the known service before content-matching.

---

## Type Hints

Added only to files being touched — no gratuitous additions.

**`subgrab.py` — core methods:**
```python
def resolve_domain(self, subdomain: str) -> list[str]: ...
def is_valid_subdomain(self, sub: str) -> bool: ...
def check_subdomain_takeover(self, sub: str) -> bool: ...
async def _check_subdomain_async(self, sub: str, session: aiohttp.ClientSession) -> dict: ...
def shodan_active_ip_scan(self) -> None: ...
def generate_reports(self) -> None: ...
```

**`modules/base.py`:**
```python
class BaseScanner:
    def run(self) -> set[str]: ...
    def resolve_domain(self, sub: str) -> list[str]: ...
    def is_valid(self, sub: str) -> bool: ...
```

**`ai_engine/base.py`:**
```python
class BaseAIEngine:
    def run(self, existing: set[str]) -> set[str]: ...
```

The four bug-fixed modules (`04`, `05`, `07`, `08`) get type hints on `run()` and any changed helpers.

---

## Test Suite

**Location:** `tests/` — runnable with `pytest`

```
tests/
├── test_validation.py       # subdomain regex, wildcard filter, is_valid_subdomain
├── test_takeover.py         # takeover detection logic, false positive fixes
├── test_bug_fixes.py        # unit tests for each of the 7 bug fixes
├── test_async_recon.py      # async HTTP/SSH check with mocked aiohttp + asyncio
├── test_modules.py          # run() returns set[str], handles network errors gracefully
└── test_reports.py          # JSON/CSV/HTML output structure for known input
```

**Key test cases:**
- `test_validation.py`: valid subdomains pass; IPs/URLs/HTML-chars/empty strings reject; wildcard IPs filtered
- `test_takeover.py`: `'404'`/`'Not Found'` no longer triggers; real CNAME + content match still triggers
- `test_bug_fixes.py`: WhoisXML strips `*.*.example.com` → `example.com`; GitHub 422 falls back; module 04 calls resolver not socket
- `test_async_recon.py`: mocked `aiohttp.ClientSession` returns 200/404/timeout; results land in `subdomain_info` correctly; semaphore limits concurrency
- `test_modules.py`: each module's `run()` returns a `set`, handles `requests.Timeout`/`requests.ConnectionError` without raising
- `test_reports.py`: given a fixed `subdomain_info` dict, JSON has expected keys; CSV has correct headers; HTML contains subdomain name

No live network calls in tests — all external I/O mocked with `pytest-mock` / `unittest.mock` / `aioresponses`.

**New dev dependencies:**
```
pytest>=7.0
pytest-asyncio>=0.23
pytest-mock>=3.0
aioresponses>=0.7
```

---

## Summary of Changes per File

| File | Change type |
|------|-------------|
| `subgrab.py` | Async active recon, bug fixes 1/5/7, type hints |
| `modules/04_dns_databases.py` | Bug fix 2, type hints |
| `modules/05_whoisxml.py` | Bug fix 3, type hints |
| `modules/07_github_search.py` | Bug fix 4, type hints |
| `modules/08_dns_bruteforce.py` | Bug fix 6, type hints |
| `modules/base.py` | Type hints on interface |
| `ai_engine/base.py` | Type hints on interface |
| `requirements.txt` | Add `aiohttp>=3.9.0` |
| `requirements-dev.txt` | New file: pytest deps |
| `tests/` | New directory: 6 test files |
