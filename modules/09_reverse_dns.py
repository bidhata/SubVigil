from __future__ import annotations
import dns.exception
import dns.resolver
import dns.reversename

from colorama import Fore
from modules.base import BaseScanner


class ReverseDNS(BaseScanner):
    name = "Reverse DNS"
    description = "Reverse DNS lookups on IP neighbours"
    fast_mode_skip = True

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Performing reverse DNS lookups...")
        subdomains = set()

        try:
            main_ips = self.resolve_domain(self.domain)
            if main_ips:
                for ip in main_ips:
                    # Skip IPv6 addresses
                    if ":" in ip:
                        continue
                    ip_parts = ip.split(".")
                    if len(ip_parts) != 4:
                        continue
                    try:
                        last = int(ip_parts[3])
                    except ValueError:
                        continue
                    base_ip = ".".join(ip_parts[:3])
                    # Scan ±10 neighbours; range end is exclusive so +11 covers last+10
                    for i in range(max(1, last - 10), min(254, last + 11)):
                        try:
                            ptr_name = dns.reversename.from_address(f"{base_ip}.{i}")
                            answers = self.get_resolver().resolve(ptr_name, 'PTR')
                            if not answers:
                                continue
                            hostname = str(answers[0]).rstrip('.').lower()
                            if hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                subdomains.add(hostname)
                        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                                dns.resolver.Timeout, dns.exception.DNSException,
                                IndexError):
                            pass
        except Exception as e:
            print(f"{Fore.RED}[!] Error with reverse DNS: {e}")

        return subdomains
