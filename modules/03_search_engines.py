import re
from urllib.parse import quote_plus

from colorama import Fore
from modules.base import BaseScanner


class SearchEngines(BaseScanner):
    name = "Search Engines"
    description = "Bing, DuckDuckGo, Yahoo search dorks (Google fallback)"

    # Browsers rotate to avoid trivial bot detection
    _UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def run(self):
        print(f"{Fore.CYAN}[*] Searching search engines...")
        subdomains = set()

        sources = [
            ("Bing",       self._search_bing),
            ("DuckDuckGo", self._search_ddg),
            ("Yahoo",      self._search_yahoo),
            ("Google",     self._search_google),
        ]

        for engine, method in sources:
            try:
                found = method()
                if found:
                    subdomains.update(found)
                    print(f"{Fore.GREEN}[+] {engine}: {len(found)} subdomains")
                else:
                    print(f"{Fore.YELLOW}[!] {engine}: 0 results")
            except Exception as e:
                print(f"{Fore.YELLOW}[!] {engine}: {str(e)[:80]}")
            self.stealth_delay()

        return subdomains

    # ------------------------------------------------------------------ #

    def _extract(self, text):
        """Pull any *.domain strings out of a blob of text."""
        pattern = r"(?:https?://)?([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\." + re.escape(self.domain) + r")"
        found = set()
        for m in re.findall(pattern, text):
            m = m.lower().strip(".")
            if m.endswith(f".{self.domain}") and self.is_valid(m):
                found.add(m)
        return found

    def _get(self, url, extra_headers=None):
        headers = {"User-Agent": self._UA, "Accept-Language": "en-US,en;q=0.9"}
        if extra_headers:
            headers.update(extra_headers)
        return self.get_session().get(url, headers=headers, timeout=15)

    # ---- Bing ----
    def _search_bing(self):
        subdomains = set()
        queries = [
            f"site:{self.domain}",
            f"site:*.{self.domain}",
        ]
        for q in queries:
            for first in range(1, 91, 10):   # pages 1-10
                url = f"https://www.bing.com/search?q={quote_plus(q)}&first={first}&count=10"
                r = self._get(url)
                if r.status_code != 200:
                    break
                found = self._extract(r.text)
                prev = len(subdomains)
                subdomains.update(found)
                if len(subdomains) == prev and first > 1:
                    break   # no new results on this page — stop paginating
            self.stealth_delay()
        return subdomains

    # ---- DuckDuckGo HTML endpoint ----
    def _search_ddg(self):
        subdomains = set()
        queries = [
            f"site:{self.domain}",
            f"site:*.{self.domain}",
        ]
        for q in queries:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
            r = self._get(url, {"Accept": "text/html"})
            if r.status_code == 200:
                subdomains.update(self._extract(r.text))
            self.stealth_delay()
        return subdomains

    # ---- Yahoo ----
    def _search_yahoo(self):
        subdomains = set()
        queries = [
            f"site:{self.domain}",
            f"site:*.{self.domain}",
        ]
        for q in queries:
            for b in range(1, 51, 10):   # first 5 pages
                url = f"https://search.yahoo.com/search?p={quote_plus(q)}&b={b}&pz=10"
                r = self._get(url)
                if r.status_code != 200:
                    break
                found = self._extract(r.text)
                prev = len(subdomains)
                subdomains.update(found)
                if len(subdomains) == prev and b > 1:
                    break
            self.stealth_delay()
        return subdomains

    # ---- Google (last resort — often 429/CAPTCHA) ----
    def _search_google(self):
        subdomains = set()
        queries = [
            f"site:*.{self.domain}",
            f"site:{self.domain} -www",
        ]
        for q in queries:
            url = f"https://www.google.com/search?q={quote_plus(q)}&num=100"
            r = self._get(url)
            if r.status_code == 200:
                subdomains.update(self._extract(r.text))
            self.stealth_delay()
        return subdomains
