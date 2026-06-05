"""
c99.nl SubdomainFinder scraper.

Pulls subdomains from https://subdomainfinder.c99.nl/scans/<YYYY-MM-DD>/<domain>.
The site renders the full list (same data backing the "Download CSV" button)
into the HTML table, so we parse the table directly.

Walks back day-by-day from today until a cached scan is found or the lookback
limit is reached. Captures per-row IP and Cloudflare flags (class="sd"/ip/cf),
merges IPs into self.subdomain_info, and writes a side-car
<output_dir>/<domain>_c99_scan.json.

c99 actively blocks scrapers; if the abuse banner is detected we abort the walk.
"""

import datetime
import json
import os
import re
import time

from bs4 import BeautifulSoup
from colorama import Fore
from modules.base import BaseScanner


class C99SubdomainFinder(BaseScanner):
    name = "c99.nl SubdomainFinder"
    description = "subdomainfinder.c99.nl scan results"
    fast_mode_skip = False

    BASE = "https://subdomainfinder.c99.nl"
    LOOKBACK_DAYS = 60 
 
    ABUSE_MARKERS = ("Abuse has been detected", "cheap API key")

    def run(self) -> set[str]:
        if os.environ.get("SUBVIGIL_DISABLE_C99") == "1":
            print(f"{Fore.YELLOW}[*] c99.nl SubdomainFinder: skipped (SUBVIGIL_DISABLE_C99=1)")
            return set()
        print(f"{Fore.CYAN}[*] Querying c99.nl SubdomainFinder...")
        subdomains: set[str] = set()
        domain = self.domain.lower().strip(".")
        session = self.get_session()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"{self.BASE}/",
        }

        today = datetime.date.today()
        scan_url = None
        html = None

        for offset in range(self.LOOKBACK_DAYS + 1):
            day = today - datetime.timedelta(days=offset)
            url = f"{self.BASE}/scans/{day.isoformat()}/{domain}"
            try:
                resp = session.get(
                    url, headers=headers, timeout=self.timeout, allow_redirects=True
                )
            except Exception as e:
                print(f"{Fore.YELLOW}[!] c99.nl request failed for {day}: {e}")
                self.stealth_delay()
                continue

            text = resp.text or ""
            if any(m in text for m in self.ABUSE_MARKERS):
                print(
                    f"{Fore.RED}[!] c99.nl blocked the request (abuse detection). "
                    f"A paid c99 API key is required for automated scans."
                )
                return subdomains
            if resp.status_code == 429:
                print(f"{Fore.YELLOW}[!] c99.nl rate-limited (429); backing off 5s")
                time.sleep(5)
                continue
            if resp.status_code != 200:
                self.stealth_delay()
                continue
            if f".{domain}" not in text:
                self.stealth_delay()
                continue

            scan_url = resp.url
            html = text
            print(f"{Fore.GREEN}[+] Found c99.nl scan: {scan_url} ({len(html):,} bytes)")
            break

        if not html:
            print(
                f"{Fore.YELLOW}[!] No c99.nl scan found in last "
                f"{self.LOOKBACK_DAYS} days for {domain}"
            )
            return subdomains

        try:
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")

            c99_data = []
            suffix = f".{domain}"

            # Primary: per-row structured extraction (subdomain + IP + Cloudflare).
            sd_elements = soup.find_all(class_="sd")
            if not sd_elements:
                for alt in ("subdomain", "host", "domain", "sub", "name"):
                    alt_elems = soup.find_all(class_=alt)
                    if alt_elems:
                        sd_elements = alt_elems
                        break

            for sd_elem in sd_elements:
                host = sd_elem.get_text(strip=True).lower()
                if not host.endswith(suffix) or not self.is_valid(host):
                    continue
                subdomains.add(host)
                row = sd_elem.find_parent("tr")
                if not row:
                    continue
                ip_elem = row.find(class_="ip")
                cf_elem = row.find(class_="cf")
                ip = ip_elem.get_text(strip=True) if ip_elem else ""
                cloudflare = None
                if cf_elem:
                    img = cf_elem.find("img")
                    if img and img.get("data-cf"):
                        cloudflare = img["data-cf"]
                c99_data.append({"subdomain": host, "ip": ip, "cloudflare": cloudflare})
                if ip and host not in self.subdomain_info:
                    self.subdomain_info[host] = {"ip": ip, "source": "c99"}

            # Fallback regex sweep so we never miss hosts even if layout changes.
            # Negative lookbehind/lookahead avoids matching inside foo.<domain>.evil.com.
            pattern = re.compile(
                r"(?<![A-Za-z0-9_.-])"
                r"([a-z0-9_][a-z0-9_.\-]*\." + re.escape(domain) + r")"
                r"(?![A-Za-z0-9_.-])",
                re.IGNORECASE,
            )
            for match in pattern.findall(html):
                host = match.lower().strip(".")
                if host != domain and self.is_valid(host):
                    subdomains.add(host)

            if c99_data:
                out = os.path.join(self.output_dir, f"{domain}_c99_scan.json")
                try:
                    with open(out, "w", encoding="utf-8") as f:
                        json.dump(c99_data, f, indent=2, ensure_ascii=False)
                    print(f"{Fore.GREEN}[+] c99 scan data saved to {out}")
                except Exception as e:
                    print(f"{Fore.YELLOW}[!] Failed to write c99 side-car: {e}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error parsing c99.nl scan: {e}")

        if subdomains:
            print(
                f"{Fore.GREEN}[+] c99.nl SubdomainFinder: "
                f"{len(subdomains)} subdomains"
            )
        return subdomains
