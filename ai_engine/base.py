"""
SubVigil AI Engine plugin system.

HOW TO ADD A NEW AI ENGINE
───────────────────────────
1. Create a .py file in this folder  →  e.g. my_llm.py
2. Write a class that inherits BaseAIEngine and implements run() → set[str]
3. Drop the file here.  It is picked up automatically on the next run.
   Delete the file to stop using that engine — nothing else to change.

AI engines run AFTER all passive scanners complete, so self.subdomains
already contains every passively discovered subdomain when run() is called.

MINIMAL PLUGIN:

    from ai_engine.base import BaseAIEngine
    from colorama import Fore

    class MyLLM(BaseAIEngine):
        name        = "My LLM"
        description = "Subdomain generation via My LLM"
        requires_key = "my_llm"   # key name in api_keys dict

        def run(self):
            key = self.api_keys["my_llm"]
            existing = [s.replace(f".{self.domain}", "")
                        for s in self.subdomains]
            # ... call your LLM API ...
            return {"sub1." + self.domain, "sub2." + self.domain}

AVAILABLE INSIDE run()
  self.domain          – target domain string
  self.api_keys        – dict of configured API keys
  self.subdomains      – set of ALL passively discovered subdomains (read-only)
  self.subdomain_info  – per-subdomain metadata dict
  self.output_dir      – path to results directory
  self.fast_mode       – True when --fast flag was passed
  self.threads         – thread count setting
  self.timeout         – request timeout in seconds
  self.get_session()   – thread-local requests.Session
  self.get_resolver()  – thread-local dns.resolver.Resolver
  self.resolve_domain(sub)  – resolve subdomain → list[str] IPs or None
  self.is_valid(sub)        – validate subdomain format → bool

EXECUTION ORDER
  Files are sorted alphabetically.  Use numeric prefixes (01_, 02_, …) to
  control the order.  Files whose name starts with '_' are skipped.
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path


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

    # ------------------------------------------------------------------ #
    # Proxies — access enumerator state without boilerplate               #
    # ------------------------------------------------------------------ #

    _PROXY_ATTRS = frozenset({
        'domain', 'timeout', 'threads', 'api_keys', 'subdomains',
        'subdomain_info', 'output_dir', 'fast_mode', 'wordlist', 'default_wordlist',
    })

    def __getattr__(self, name: str):
        if name in type(self)._PROXY_ATTRS:
            return getattr(self.enumerator, name)
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def get_session(self):
        return self.enumerator.get_session()

    def get_resolver(self):
        return self.enumerator.get_resolver()

    def resolve_domain(self, subdomain: str) -> list[str] | None:
        return self.enumerator.resolve_domain(subdomain)

    def is_valid(self, subdomain: str) -> bool:
        return self.enumerator._is_valid_subdomain(subdomain)


# ──────────────────────────────────────────────────────────────────────────────

def load_ai_engines(ai_engine_dir: Path) -> list:
    """Auto-discover and load every BaseAIEngine plugin in ai_engine_dir.

    Returns an ordered list of engine classes ready to be instantiated.
    """
    project_root = str(ai_engine_dir.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from ai_engine.base import BaseAIEngine as _Base  # noqa: F401

    try:
        from colorama import Fore as _Fore
    except ImportError:
        _Fore = None

    engines = []
    failed = []

    for path in sorted(ai_engine_dir.glob("*.py")):
        if path.stem.startswith("_") or path.stem == "base":
            continue
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if not spec:
                failed.append(path.name)
                print(f"{(_Fore.RED if _Fore else '')}[!] Could not create module spec for {path.name}{(_Fore.RESET if _Fore else '')}")
                continue
            if not spec.loader:
                failed.append(path.name)
                print(f"{(_Fore.RED if _Fore else '')}[!] No loader for module {path.name}{(_Fore.RESET if _Fore else '')}")
                continue
            mod = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(mod)

            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, _Base) and obj is not _Base:
                    engines.append(obj)

        except Exception as exc:
            failed.append(path.name)
            print(f"[!] Failed to load AI engine {path.name}: {exc}")

    tag = _Fore.CYAN if _Fore else ""
    rst = _Fore.RESET if _Fore else ""
    names = ", ".join(cls.name or cls.__name__ for cls in engines)
    print(f"{tag}[*] Loaded {len(engines)} AI engine(s): {names if engines else 'none'}{rst}")
    if failed:
        err = _Fore.RED if _Fore else ""
        print(f"{err}[!] Failed to load: {', '.join(failed)}{rst}")

    return engines
