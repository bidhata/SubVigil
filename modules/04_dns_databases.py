"""
DNS database sources: C99 SubdomainFinder, DNSdumpster, HackerTarget.
Tries each in order, stops after the first that returns results.
"""

import json
import os
import re
import socket
import subprocess
import tempfile
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from colorama import Fore
from modules.base import BaseScanner


class DnsDatabases(BaseScanner):
    name = "DNS Databases"
    description = "C99 SubdomainFinder → DNSdumpster → HackerTarget"

    def run(self):
        print(f"{Fore.CYAN}[*] Searching DNS databases...")
        subdomains = set()

        sources = [
            ("C99 SubFinder", self._try_c99),
            ("DNSdumpster", self._try_dnsdumpster),
            ("HackerTarget", self._try_hackertarget),
        ]

        for source_name, method in sources:
            try:
                print(f"{Fore.YELLOW}[*] Trying {source_name}...")
                results = method()
                if results:
                    subdomains.update(results)
                    print(f"{Fore.GREEN}[+] {source_name}: {len(results)} subdomains")
                    break
                else:
                    print(f"{Fore.YELLOW}[!] {source_name}: No results")
            except Exception as e:
                print(f"{Fore.YELLOW}[!] {source_name}: {str(e)[:60]}")

        return subdomains

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _try_c99(self):
        subdomains = set()
        today = datetime.now()
        scan_dates = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(14)]

        content = None
        curl_available = True

        print(f"{Fore.YELLOW}[*] Searching C99 scans for {self.domain} (last 14 days)...")

        for scan_date in scan_dates:
            url = f"https://subdomainfinder.c99.nl/scans/{scan_date}/{self.domain}"

            if curl_available:
                tmp_fd, tmp_file = tempfile.mkstemp(suffix=".html")
                os.close(tmp_fd)
                try:
                    cmd = [
                        "curl", "-s", "-L",
                        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "-H", "Accept-Language: en-US,en;q=0.5",
                        "-H", "Referer: https://subdomainfinder.c99.nl/",
                        "--max-time", "180",
                        "-o", tmp_file,
                        "-w", "%{http_code}",
                        url,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=190)
                    http_code = result.stdout.strip()
                    if result.returncode == 0 and os.path.exists(tmp_file):
                        file_size = os.path.getsize(tmp_file)
                        if http_code == "404" or file_size < 1000:
                            continue
                        if file_size > 100000 and http_code == "200":
                            with open(tmp_file, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            print(f"{Fore.GREEN}[+] Found C99 scan: {scan_date} ({file_size:,} bytes)")
                            break
                        else:
                            print(f"{Fore.YELLOW}[!] Scan {scan_date}: too small ({file_size:,} bytes) or HTTP {http_code}")
                except subprocess.TimeoutExpired:
                    print(f"{Fore.YELLOW}[!] Timeout for {scan_date}")
                except FileNotFoundError:
                    print(f"{Fore.RED}[!] curl not found - falling back to requests")
                    curl_available = False
                finally:
                    try:
                        if os.path.exists(tmp_file):
                            os.unlink(tmp_file)
                    except Exception:
                        pass

            if not curl_available:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://subdomainfinder.c99.nl/",
                    }
                    response = self.get_session().get(url, headers=headers, timeout=120)
                    if response.status_code == 404:
                        continue
                    if response.status_code == 200 and len(response.text) > 100000:
                        content = response.text
                        print(f"{Fore.GREEN}[+] Found C99 scan: {scan_date} ({len(content):,} bytes)")
                        break
                except Exception as e:
                    print(f"{Fore.YELLOW}[!] C99 requests fallback error: {str(e)[:60]}")

        if not content:
            print(f"{Fore.YELLOW}[!] No valid C99 scan found for {self.domain} in the last 14 days")
            return subdomains

        print(f"{Fore.CYAN}[*] Parsing C99 scan results...")

        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        sd_elements = soup.find_all(class_="sd")

        # Try alternative class names if layout changed
        if not sd_elements:
            for alt in ("subdomain", "host", "domain", "sub", "name"):
                alt_elems = soup.find_all(class_=alt)
                if alt_elems:
                    sd_elements = alt_elems
                    print(f"{Fore.CYAN}[*] Found {len(sd_elements)} entries using class='{alt}'")
                    break

        # Regex fallback over raw HTML
        if not sd_elements:
            pattern = re.compile(r"[\w][\w\-]*(?:\.[\w\-]+)*\." + re.escape(self.domain))
            for m in re.findall(pattern, content):
                m = m.strip().lower()
                if m.endswith(f".{self.domain}") and self.is_valid(m):
                    subdomains.add(m)
            if subdomains:
                print(f"{Fore.CYAN}[*] Regex fallback found {len(subdomains)} subdomains from C99 page")
            else:
                print(f"{Fore.YELLOW}[!] C99 page structure unrecognised - 0 subdomains extracted")

        if sd_elements:
            print(f"{Fore.CYAN}[*] Found {len(sd_elements)} subdomain entries in scan")

        c99_data = []
        for sd_elem in sd_elements:
            text = sd_elem.get_text(strip=True)
            if not text or not text.endswith(f".{self.domain}"):
                continue
            if self.is_valid(text):
                subdomains.add(text)
                row = sd_elem.find_parent("tr")
                if row:
                    ip_elem = row.find(class_="ip")
                    cf_elem = row.find(class_="cf")
                    ip = ip_elem.get_text(strip=True) if ip_elem else ""
                    cloudflare = None
                    if cf_elem:
                        img = cf_elem.find("img")
                        if img and img.get("data-cf"):
                            cloudflare = img["data-cf"]
                    c99_data.append({"subdomain": text, "ip": ip, "cloudflare": cloudflare})
                    if ip and text not in self.subdomain_info:
                        self.subdomain_info[text] = {"ip": ip, "source": "c99"}

        if c99_data:
            out = os.path.join(self.output_dir, f"{self.domain}_c99_scan.json")
            try:
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(c99_data, f, indent=2, ensure_ascii=False)
                print(f"{Fore.GREEN}[+] C99 scan data saved to {out}")
            except Exception:
                pass

        print(f"{Fore.CYAN}[*] C99 SubFinder: Extracted {len(subdomains)} unique subdomains")
        return subdomains

    def _try_dnsdumpster(self) -> set[str]:
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
            response = self.get_session().get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code == 200:
                for line in response.text.strip().split("\n"):
                    if "," in line:
                        hostname = line.split(",")[0].strip()
                        if hostname.endswith(f".{self.domain}"):
                            subdomains.add(hostname)
        except Exception:
            pass
        return subdomains
