"""
c99.nl SubdomainFinder.

c99 exposes subdomain data two ways:

1. Official API (reliable): https://api.c99.nl/subdomainfinder?key=<KEY>&domain=<D>&json
   Returns JSON {"success": bool, "subdomains": [{"subdomain", "ip", "cloudflare"}...]}.
   Used automatically when a "c99" API key is configured. This is the ONLY
   method c99 supports for automation.

2. HTML scrape (best-effort fallback): https://subdomainfinder.c99.nl/
   The public site is behind Cloudflare and actively blocks scrapers — any
   automated request to a scan path is answered with a 200 "Abuse has been
   detected" page. We attempt a single best-effort fetch; if the abuse banner
   (or no usable scan) is seen, we give up quietly. Without a key this source
   will usually return nothing, which is expected — other sources cover it.

Per-row IP and Cloudflare flags are merged into self.subdomain_info and written
to a side-car <output_dir>/<domain>_c99_scan.json.

Set SUBVIGIL_DISABLE_C99=1 to skip this module entirely.
"""

import json
import os
import re

from bs4 import BeautifulSoup
from colorama import Fore
from modules.base import BaseScanner


class C99SubdomainFinder(BaseScanner):
    name = "c99.nl SubdomainFinder"
    description = "c99.nl SubdomainFinder (official API, HTML fallback)"
    fast_mode_skip = False
    requires_key = None  # key is optional; module still runs without it

    BASE = "https://subdomainfinder.c99.nl"
    API = "https://api.c99.nl/subdomainfinder"

    ABUSE_MARKERS = ("Abuse has been detected", "cheap API key")

    def run(self) -> set[str]:
        if os.environ.get("SUBVIGIL_DISABLE_C99") == "1":
            print(f"{Fore.YELLOW}[*] c99.nl SubdomainFinder: skipped (SUBVIGIL_DISABLE_C99=1)")
            return set()
        print(f"{Fore.CYAN}[*] Querying c99.nl SubdomainFinder...")

        domain = self.domain.lower().strip(".")

        # 1) Official API — the only reliable, non-abusive path.
        api_key = (self.api_keys or {}).get("c99")
        if api_key:
            subs = self._query_api(domain, api_key)
            if subs is not None:
                return subs
            # API failed (bad key / error); fall through to best-effort scrape.

        # 2) HTML fallback — expected to be blocked without a key.
        return self._scrape(domain)

    # ------------------------------------------------------------------ #
    # Official API                                                        #
    # ------------------------------------------------------------------ #
    def _query_api(self, domain: str, api_key: str):
        """Return a set of subdomains, or None if the API call failed."""
        subdomains: set[str] = set()
        c99_data = []
        try:
            resp = self.get_session().get(
                self.API,
                params={"key": api_key, "domain": domain, "json": ""},
                timeout=self.timeout,
            )
        except Exception as e:
            print(f"{Fore.YELLOW}[!] c99 API request failed: {e}")
            return None

        try:
            data = resp.json()
        except Exception:
            print(f"{Fore.YELLOW}[!] c99 API returned non-JSON response")
            return None

        if not data.get("success"):
            print(f"{Fore.RED}[!] c99 API error: {data.get('error', 'unknown error')}")
            return None

        for entry in data.get("subdomains", []):
            host = str(entry.get("subdomain", "")).lower().strip(".")
            if not host.endswith(f".{domain}") or not self.is_valid(host):
                continue
            subdomains.add(host)
            ip = str(entry.get("ip", "") or "")
            cloudflare = entry.get("cloudflare")
            c99_data.append({"subdomain": host, "ip": ip, "cloudflare": cloudflare})
            if ip and host not in self.subdomain_info:
                self.subdomain_info[host] = {"ip": ip, "source": "c99"}

        self._write_sidecar(domain, c99_data)
        if subdomains:
            print(f"{Fore.GREEN}[+] c99 API: {len(subdomains)} subdomains")
        else:
            print(f"{Fore.YELLOW}[!] c99 API: no subdomains for {domain}")
        return subdomains

    # ------------------------------------------------------------------ #
    # HTML scrape fallback                                                #
    # ------------------------------------------------------------------ #
    def _scrape(self, domain: str) -> set[str]:
        subdomains: set[str] = set()
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

        url = f"{self.BASE}/scans/{domain}"
        try:
            resp = session.get(
                url, headers=headers, timeout=self.timeout, allow_redirects=True
            )
        except Exception as e:
            print(f"{Fore.YELLOW}[!] c99.nl request failed: {e}")
            return subdomains

        text = resp.text or ""
        if any(m in text for m in self.ABUSE_MARKERS):
            print(
                f"{Fore.YELLOW}[!] c99.nl blocked the scrape (Cloudflare abuse page). "
                f"Configure a 'c99' API key for reliable results — skipping."
            )
            return subdomains
        if resp.status_code != 200 or f".{domain}" not in text:
            print(f"{Fore.YELLOW}[!] c99.nl: no usable scan page for {domain}")
            return subdomains

        html = text
        print(f"{Fore.GREEN}[+] c99.nl scan page: {resp.url} ({len(html):,} bytes)")

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

            self._write_sidecar(domain, c99_data)
        except Exception as e:
            print(f"{Fore.RED}[!] Error parsing c99.nl scan: {e}")

        if subdomains:
            print(
                f"{Fore.GREEN}[+] c99.nl SubdomainFinder: "
                f"{len(subdomains)} subdomains"
            )
        return subdomains

    # ------------------------------------------------------------------ #
    # Shared helper                                                       #
    # ------------------------------------------------------------------ #
    def _write_sidecar(self, domain: str, c99_data: list) -> None:
        """Persist per-row IP / Cloudflare data to <output_dir>/<domain>_c99_scan.json."""
        if not c99_data:
            return
        out = os.path.join(self.output_dir, f"{domain}_c99_scan.json")
        try:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(c99_data, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}[+] c99 scan data saved to {out}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Failed to write c99 side-car: {e}")
