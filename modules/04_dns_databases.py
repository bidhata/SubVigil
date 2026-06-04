"""
DNS database sources: HackerTarget + common-label resolution fallback.

C99 SubdomainFinder is handled by 10_c99_subdomainfinder.py.

All sources run and their results are unioned (no break-on-first-success).
"""

from colorama import Fore
from modules.base import BaseScanner


class DnsDatabases(BaseScanner):
    name = "DNS Databases"
    description = "HackerTarget + common-label DNS resolution"

    def run(self):
        print(f"{Fore.CYAN}[*] Searching DNS databases...")
        subdomains = set()

        sources = [
            ("HackerTarget", self._try_hackertarget),
            ("Common labels", self._try_common_labels),
        ]

        for source_name, method in sources:
            try:
                print(f"{Fore.YELLOW}[*] Trying {source_name}...")
                results = method()
                if results:
                    subdomains.update(results)
                    print(f"{Fore.GREEN}[+] {source_name}: {len(results)} subdomains")
                else:
                    print(f"{Fore.YELLOW}[!] {source_name}: No results")
            except Exception as e:
                print(f"{Fore.YELLOW}[!] {source_name}: {str(e)[:60]}")

        return subdomains

    def _try_common_labels(self) -> set[str]:
        """Resolve a small set of well-known labels against the target domain."""
        subdomains = set()
        common_subs = ["www", "mail", "ftp", "admin", "api", "blog", "dev", "test", "staging"]
        for sub in common_subs:
            full = f"{sub}.{self.domain}"
            if self.resolve_domain(full):
                subdomains.add(full)
        return subdomains

    def _try_hackertarget(self):
        subdomains = set()
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
            response = self.get_session().get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
            )
            if response.status_code == 200:
                for line in response.text.strip().split("\n"):
                    if "," in line:
                        hostname = line.split(",")[0].strip()
                        if hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                            subdomains.add(hostname)
        except Exception:
            pass
        return subdomains
