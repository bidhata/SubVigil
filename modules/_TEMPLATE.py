# ─────────────────────────────────────────────────────────────────────────────
# SubVigil Scanner Plugin Template
#
# HOW TO USE:
#   1. Copy this file, rename it  e.g. 12_my_source.py
#   2. Fill in name, description, and the run() method
#   3. Drop the file in this folder — it loads automatically next scan
#   4. Delete the file to disable it — nothing else to change
#
# The loader pre-injects `Fore` for colored output, but for static analysis
# and type checking, it's best to import `BaseScanner` and `Fore` explicitly.
# ─────────────────────────────────────────────────────────────────────────────

from colorama import Fore
from modules.base import BaseScanner


class MySource(BaseScanner):
    name         = "My Source"         # shown in logs and startup list
    description  = "One-line description of what this scanner does"

    # ── optional flags ────────────────────────────────────────────────────
    requires_key   = None    # set to an api_keys key, e.g. "shodan"
                             # scanner is auto-skipped when that key is absent
    fast_mode_skip = False   # set True to skip when --fast flag is passed
    # ──────────────────────────────────────────────────────────────────────

    def run(self):
        """Return a set of discovered subdomain strings."""
        subdomains = set()

        try:
            # Example: query an HTTP API
            url = f"https://api.example.com/subdomains?domain={self.domain}"
            response = self.get_session().get(url, timeout=10)

            if response.status_code == 200:
                for entry in response.json():
                    host = entry.get("hostname", "").strip().lower()
                    if host.endswith(f".{self.domain}") and self.is_valid(host):
                        subdomains.add(host)
            else:
                print(f"{Fore.YELLOW}[!] {self.name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"{Fore.RED}[!] {self.name} error: {e}")

        return subdomains


# ─────────────────────────────────────────────────────────────────────────────
# QUICK REFERENCE — everything available inside run()
#
#   self.domain            target domain string  (e.g. "example.com")
#   self.api_keys          dict of configured API keys
#   self.subdomains        subdomains found so far by earlier modules (read-only)
#   self.subdomain_info    per-subdomain metadata dict
#   self.output_dir        path to the results directory
#   self.fast_mode         True when --fast was passed
#   self.threads           thread count
#   self.timeout           HTTP/DNS timeout in seconds
#   self.wordlist          custom wordlist path, or None
#   self.default_wordlist  built-in wordlist (list of strings)
#
#   self.get_session()               thread-local requests.Session
#   self.get_resolver()              thread-local dns.resolver.Resolver
#   self.resolve_domain(sub)         → list[str] IPs  or  None
#   self.is_valid(sub)               → bool  (format + domain check)
#   self.stealth_delay()             sleep 0.5-2s when --stealth is on
#   self.shodan_scan()               Shodan scan on active IPs (needs key)
#   self.extract_from_json(data)     pull subdomains from arbitrary JSON
#   self.extract_from_page(soup, t)  pull subdomains from BeautifulSoup + text
#
#   Fore.RED / GREEN / CYAN / YELLOW / RESET   (colorama, pre-injected)
# ─────────────────────────────────────────────────────────────────────────────
