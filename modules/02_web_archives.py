import json
import time
from urllib.parse import urlparse
import requests

from colorama import Fore
from modules.base import BaseScanner


class WebArchives(BaseScanner):
    name = "Web Archives"
    description = "Search Wayback Machine and CommonCrawl"

    def _latest_commoncrawl_index(self):
        """Return the API URL for the most recent CommonCrawl index, or None."""
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
        return None

    def run(self):
        print(f"{Fore.CYAN}[*] Searching web archives...")
        all_subdomains = set()

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
        ]
        if cc_url:
            sources.append({
                "name": "CommonCrawl Index",
                "url": f"{cc_url}?url=*.{self.domain}/*&output=json&fl=url",
                "timeout": 25,
            })
        else:
            print(f"{Fore.YELLOW}[!] CommonCrawl: latest index unavailable, skipping")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        }

        any_source_succeeded = False
        for source in sources:
            print(f"{Fore.YELLOW}[*] Trying {source['name']}...")
            response = None
            source_subdomains = set()

            for attempt in range(3):
                try:
                    response = self.get_session().get(
                        source["url"], timeout=source["timeout"], headers=headers
                    )
                    if response.status_code == 200:
                        any_source_succeeded = True
                        break  # Success, break retry loop

                    if response.status_code in (429, 502, 503, 504):
                        if attempt < 2:
                            wait = 5 * (2 ** attempt)
                            print(f"{Fore.YELLOW}[!] {source['name']}: HTTP {response.status_code}, retrying in {wait}s...")
                            time.sleep(wait)
                            continue  # To next attempt

                    print(f"{Fore.YELLOW}[!] {source['name']}: HTTP {response.status_code}")
                    break  # Don't retry for other errors

                except requests.exceptions.RequestException as e:
                    if isinstance(e, requests.exceptions.Timeout):
                        err_msg = "Connection timed out"
                    elif isinstance(e, requests.exceptions.ConnectionError):
                        err_msg = "Connection error"
                    else:
                        err_msg = str(e).split(':')[-1].strip() or str(e)
                        
                    if attempt < 2:
                        wait = 5 * (attempt + 1)
                        print(f"{Fore.YELLOW}[!] {source['name']}: {err_msg[:100]}, retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"{Fore.YELLOW}[!] {source['name']}: {err_msg[:100]}")
                    response = None # Ensure response is None on failure

            if response and response.status_code == 200:
                try:
                    if "commoncrawl" in source["url"]:
                        for line in response.text.strip().split("\n"):
                            try:
                                hostname = urlparse(json.loads(line).get("url", "")).hostname
                                if hostname and hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                    source_subdomains.add(hostname)
                            except Exception:
                                continue
                    else:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 1:
                            for item in data[1:]:
                                if isinstance(item, list) and item and isinstance(item[0], str):
                                    hostname = urlparse(item[0]).hostname
                                    if hostname and hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                        source_subdomains.add(hostname)
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] {source['name']}: Failed to decode JSON response.")

            if source_subdomains:
                print(f"{Fore.GREEN}[+] {source['name']}: Found {len(source_subdomains)} subdomains")
                all_subdomains.update(source_subdomains)
            elif response and response.status_code == 200:
                print(f"{Fore.YELLOW}[!] {source['name']}: No results")

        if not all_subdomains and not any_source_succeeded:
            print(f"{Fore.RED}[!] All web archive sources failed to respond.")

        return all_subdomains
