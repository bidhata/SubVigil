import json
from urllib.parse import urlparse

from colorama import Fore
from modules.base import BaseScanner


class WebArchives(BaseScanner):
    name = "Web Archives"
    description = "Search Wayback Machine and CommonCrawl"

    def _latest_commoncrawl_index(self):
        """Return the API URL for the most recent CommonCrawl index."""
        try:
            resp = self.get_session().get(
                "https://index.commoncrawl.org/collinfo.json", timeout=8
            )
            if resp.status_code == 200:
                indexes = resp.json()
                if indexes:
                    cdx_api = indexes[0].get("cdx-api", "")
                    if cdx_api:
                        return cdx_api
        except Exception:
            pass
        return "https://index.commoncrawl.org/CC-MAIN-2026-13-index"

    def run(self):
        print(f"{Fore.CYAN}[*] Searching web archives...")
        subdomains = set()

        cc_url = self._latest_commoncrawl_index()

        sources = [
            {
                "name": "Wayback Machine CDX",
                "url": (
                    f"https://web.archive.org/cdx/search/cdx"
                    f"?url=*.{self.domain}/*&output=json&fl=original&collapse=urlkey&limit=5000"
                ),
                "timeout": 45,
            },
            {
                "name": "Wayback Machine Alternative",
                "url": (
                    f"https://web.archive.org/cdx/search/cdx"
                    f"?url={self.domain}/*&output=json&fl=original&collapse=urlkey&limit=3000"
                ),
                "timeout": 30,
            },
            {
                "name": "CommonCrawl Index",
                "url": f"{cc_url}?url=*.{self.domain}/*&output=json&fl=url",
                "timeout": 25,
            },
        ]

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        for source in sources:
            try:
                print(f"{Fore.YELLOW}[*] Trying {source['name']}...")
                response = self.get_session().get(
                    source["url"], timeout=source["timeout"], headers=headers
                )
                if response.status_code != 200:
                    print(f"{Fore.YELLOW}[!] {source['name']}: HTTP {response.status_code}")
                    continue

                if "commoncrawl" in source["url"]:
                    for line in response.text.strip().split("\n")[:100]:
                        try:
                            hostname = urlparse(json.loads(line).get("url", "")).hostname
                            if hostname and hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                subdomains.add(hostname)
                        except Exception:
                            continue
                else:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 1:
                        for item in data[1:]:
                            if isinstance(item, list) and item and isinstance(item[0], str):
                                hostname = urlparse(item[0]).hostname
                                if hostname and hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                    subdomains.add(hostname)

                if subdomains:
                    print(f"{Fore.GREEN}[+] {source['name']}: {len(subdomains)} subdomains")
                    break
                else:
                    print(f"{Fore.YELLOW}[!] {source['name']}: No results")

            except Exception as e:
                print(f"{Fore.YELLOW}[!] {source['name']}: {str(e)[:60]}")

        if not subdomains:
            print(f"{Fore.RED}[!] All web archive sources failed")

        return subdomains
