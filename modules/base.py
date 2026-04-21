"""
SubGrab passive scanner plugin system.

HOW TO ADD A NEW SCANNER
─────────────────────────
1. Create a .py file in this folder  →  e.g. 12_my_source.py
2. Write a class that inherits BaseScanner and implements run() → set[str]
3. Drop the file here.  It is picked up automatically on the next run.
   Delete the file to stop using that scanner — nothing else to change.

MINIMAL PLUGIN (no imports needed — BaseScanner and Fore are pre-injected):

    class MySource(BaseScanner):
        name        = "My Source"        # shown in logs
        description = "What it does"

        # optional flags:
        requires_key  = None   # set to an api_keys dict key to auto-skip when absent
        fast_mode_skip = False # set True to skip when --fast is passed

        def run(self):
            subdomains = set()
            resp = self.get_session().get(
                f"https://api.example.com?q={self.domain}", timeout=10
            )
            for entry in resp.json():
                host = entry.get("hostname", "")
                if host.endswith(f".{self.domain}") and self.is_valid(host):
                    subdomains.add(host)
            return subdomains

AVAILABLE INSIDE run()
  self.domain          – target domain string
  self.api_keys        – dict of configured API keys
  self.subdomains      – set of subdomains found so far (read-only)
  self.subdomain_info  – per-subdomain metadata dict
  self.output_dir      – path to results directory
  self.fast_mode       – True when --fast flag was passed
  self.threads         – thread count setting
  self.timeout         – request timeout in seconds
  self.wordlist        – custom wordlist path or None
  self.default_wordlist – built-in wordlist (list of strings)
  self.get_session()   – thread-local requests.Session
  self.get_resolver()  – thread-local dns.resolver.Resolver
  self.resolve_domain(sub)  – resolve subdomain → list[str] IPs or None
  self.is_valid(sub)        – validate subdomain format → bool
  self.stealth_delay()      – sleep 0.5-2s when --stealth is on
  self.shodan_scan()        – run Shodan on active IPs (requires shodan key)
  self.extract_from_json(data)        – extract subdomains from arbitrary JSON
  self.extract_from_page(soup, text)  – extract subdomains from parsed HTML
  Fore.RED / GREEN / CYAN / YELLOW    – colorama colors for print output

EXECUTION ORDER
  Files are sorted alphabetically.  Use numeric prefixes (01_, 02_, …) to
  control the order.  Files whose name starts with '_' are skipped.
"""

import importlib.util
import inspect
import sys
from pathlib import Path


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

    # ------------------------------------------------------------------ #
    # Proxies — access enumerator state without boilerplate               #
    # ------------------------------------------------------------------ #

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


# ──────────────────────────────────────────────────────────────────────────────

def load_modules(modules_dir: Path) -> list:
    """Auto-discover and load every BaseScanner plugin in modules_dir.

    Returns an ordered list of scanner classes ready to be instantiated.
    Prints a one-line summary of loaded plugins.
    """
    project_root = str(modules_dir.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Canonical import so issubclass() works across all load paths.
    from modules.base import BaseScanner as _Base  # noqa: F401

    try:
        from colorama import Fore as _Fore
    except ImportError:
        _Fore = None

    scanners = []
    failed = []

    for path in sorted(modules_dir.glob("*.py")):
        if path.stem.startswith("_") or path.stem == "base":
            continue
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod = importlib.util.module_from_spec(spec)

            # ── pre-inject so plugin files need zero imports ──────────────
            mod.BaseScanner = _Base
            if _Fore is not None:
                mod.Fore = _Fore
            # ─────────────────────────────────────────────────────────────

            spec.loader.exec_module(mod)

            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, _Base) and obj is not _Base:
                    scanners.append(obj)

        except Exception as exc:
            failed.append(path.name)
            print(f"[!] Failed to load plugin {path.name}: {exc}")

    # ── startup summary ───────────────────────────────────────────────────
    names = ", ".join(cls.name or cls.__name__ for cls in scanners)
    tag = _Fore.CYAN if _Fore else ""
    rst = _Fore.RESET if _Fore else ""
    print(f"{tag}[*] Loaded {len(scanners)} scanner plugin(s): {names}{rst}")
    if failed:
        err = _Fore.RED if _Fore else ""
        print(f"{err}[!] Failed to load: {', '.join(failed)}{rst}")

    return scanners
