"""
Certificate Transparency log sources:
  1. crt.sh          (with retry + backoff)
  2. CertSpotter
  3. RapidDNS
  4. urlscan.io

All sources run independently — a rate-limit on one does not drop the total.
"""

import re
import time

from bs4 import BeautifulSoup
from colorama import Fore
from modules.base import BaseScanner


class CertificateTransparency(BaseScanner):
    name = "Certificate Transparency"
    description = "crt.sh · CertSpotter · RapidDNS · urlscan.io"

    def run(self):
        print(f"{Fore.CYAN}[*] Searching Certificate Transparency logs...")
        subdomains = set()

        sources = [
            ("crt.sh",       self._crtsh),
            ("CertSpotter",  self._certspotter),
            ("RapidDNS",     self._rapiddns),
            ("urlscan.io",   self._urlscan),
        ]

        for name, method in sources:
            try:
                found = method()
                if found:
                    subdomains.update(found)
                    print(f"{Fore.GREEN}[+] {name}: {len(found)} subdomains")
                else:
                    print(f"{Fore.YELLOW}[!] {name}: 0 results")
            except Exception as e:
                print(f"{Fore.YELLOW}[!] {name}: {str(e)[:80]}")

        return subdomains

    # ------------------------------------------------------------------ #

    def _collect(self, text_or_list):
        """Strip wildcards and collect valid subdomains from a name list."""
        found = set()
        items = text_or_list if isinstance(text_or_list, list) else [text_or_list]
        for item in items:
            name = item.strip().lstrip("*.")
            if name.endswith(f".{self.domain}") and self.is_valid(name):
                found.add(name)
        return found

    def _get(self, url, **kwargs):
        """GET with a reasonable UA header."""
        headers = kwargs.pop("headers", {})
        headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (compatible; SubGrab/2.0; +https://github.com/bidhata/SubGrab)",
        )
        return self.get_session().get(url, headers=headers, **kwargs)

    # ---- crt.sh --------------------------------------------------------

    def _crtsh(self):
        subdomains = set()
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"

        for attempt in range(3):
            try:
                r = self._get(url, timeout=90)
                if r.status_code == 200:
                    for cert in r.json():
                        for name in cert.get("name_value", "").split("\n"):
                            subdomains.update(self._collect(name))
                    return subdomains
                if r.status_code == 429:
                    wait = 10 * (2 ** attempt)
                    print(f"{Fore.YELLOW}[!] crt.sh rate-limited — retrying in {wait}s")
                    time.sleep(wait)
                    continue
                print(f"{Fore.YELLOW}[!] crt.sh HTTP {r.status_code}")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                else:
                    raise

        return subdomains

    # ---- CertSpotter ----------------------------------------------------

    def _certspotter(self):
        subdomains = set()
        url = (
            f"https://api.certspotter.com/v1/issuances"
            f"?domain={self.domain}&include_subdomains=true&expand=dns_names"
        )
        r = self._get(url, timeout=30)
        if r.status_code == 200:
            for cert in r.json():
                for dns_name in cert.get("dns_names", []):
                    subdomains.update(self._collect(dns_name))
        elif r.status_code == 429:
            print(f"{Fore.YELLOW}[!] CertSpotter: rate-limited (free tier = 100 req/hr)")
        return subdomains

    # ---- RapidDNS ------------------------------------------------------

    def _rapiddns(self):
        subdomains = set()
        url = f"https://rapiddns.io/subdomain/{self.domain}?full=1"
        r = self._get(url, timeout=30)
        if r.status_code != 200:
            print(f"{Fore.YELLOW}[!] RapidDNS: HTTP {r.status_code}")
            return subdomains

        soup = BeautifulSoup(r.text, "html.parser")
        # Results are in a table; each <td> in the first column is a hostname
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            subdomains.update(self._collect(text))

        # Also run the generic regex extractor as a fallback
        pattern = re.compile(
            r"([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
            r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\."
            + re.escape(self.domain) + r")"
        )
        for m in pattern.findall(r.text):
            host = m.lower().strip(".")
            if self.is_valid(host):
                subdomains.add(host)

        return subdomains

    # ---- urlscan.io ----------------------------------------------------

    def _urlscan(self):
        subdomains = set()
        url = f"https://urlscan.io/api/v1/search/?q=domain:{self.domain}&size=1000"
        r = self._get(url, timeout=30)
        if r.status_code == 200:
            for result in r.json().get("results", []):
                hostname = result.get("page", {}).get("domain", "")
                subdomains.update(self._collect(hostname))
        elif r.status_code == 429:
            print(f"{Fore.YELLOW}[!] urlscan.io: rate-limited")
        return subdomains
