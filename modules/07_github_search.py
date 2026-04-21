import re

from colorama import Fore
from modules.base import BaseScanner


class GitHubSearch(BaseScanner):
    name = "GitHub Code Search"
    description = "Search GitHub code and repos for domain mentions"
    fast_mode_skip = True

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Searching GitHub code...")
        subdomains = set()

        has_token = "github" in self.api_keys

        # ── 1. REST API code search ──────────────────────────────────────
        subdomains.update(self._api_code_search(has_token))

        # ── 2. HTML web scrape fallback (no auth needed) ─────────────────
        subdomains.update(self._web_search())

        return subdomains

    # ------------------------------------------------------------------ #

    def _extract(self, text: str) -> set[str]:
        pattern = (
            r"([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
            r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\."
            + re.escape(self.domain) + r")"
        )
        found = set()
        for m in re.findall(pattern, text):
            m = m.lower().strip(".")
            if m.endswith(f".{self.domain}") and self.is_valid(m):
                found.add(m)
        return found

    def _api_code_search(self, has_token: bool) -> set[str]:
        subdomains = set()
        headers = {
            # Required to receive text_matches in the response
            "Accept": "application/vnd.github.v3.text-match+json",
        }
        if has_token:
            headers["Authorization"] = f'token {self.api_keys["github"]}'

        queries = [
            f'"{self.domain}"',
            f'".{self.domain}"',
        ]

        for q in queries:
            try:
                url = f"https://api.github.com/search/code?q={q}&per_page=100"
                r = self.get_session().get(url, headers=headers, timeout=30)

                if r.status_code == 401:
                    print(f"{Fore.YELLOW}[!] GitHub: invalid token")
                    break
                if r.status_code == 403:
                    msg = r.json().get("message", "")
                    print(f"{Fore.YELLOW}[!] GitHub API: {msg[:80]}")
                    break
                if r.status_code == 422:
                    print(f"{Fore.YELLOW}[!] GitHub: API code search requires auth token; falling back to web scrape")
                    break
                if r.status_code != 200:
                    print(f"{Fore.YELLOW}[!] GitHub API: HTTP {r.status_code}")
                    break

                data = r.json()
                for item in data.get("items", []):
                    # text_matches populated when Accept header is set correctly
                    for match in item.get("text_matches", []):
                        subdomains.update(self._extract(match.get("fragment", "")))

                    # Also check the file path and repo name
                    subdomains.update(self._extract(item.get("path", "")))
                    subdomains.update(self._extract(item.get("name", "")))
                    repo = item.get("repository", {})
                    subdomains.update(self._extract(repo.get("full_name", "")))
                    subdomains.update(self._extract(repo.get("description") or ""))

            except Exception as e:
                print(f"{Fore.YELLOW}[!] GitHub API error: {str(e)[:80]}")
                break

        return subdomains

    def _web_search(self) -> set[str]:
        """Scrape github.com/search HTML as a no-auth fallback."""
        subdomains = set()
        queries = [
            f'"{self.domain}"',
            f'".{self.domain}"',
        ]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html",
        }
        for q in queries:
            try:
                url = f"https://github.com/search?q={q}&type=code"
                r = self.get_session().get(url, headers=headers, timeout=20)
                if r.status_code == 200:
                    subdomains.update(self._extract(r.text))
            except Exception:
                pass
        return subdomains
