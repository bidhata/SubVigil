import socket

from colorama import Fore
from modules.base import BaseScanner


class ReverseDNS(BaseScanner):
    name = "Reverse DNS"
    description = "Reverse DNS lookups on IP neighbours"
    fast_mode_skip = True

    def run(self):
        print(f"{Fore.CYAN}[*] Performing reverse DNS lookups...")
        subdomains = set()

        try:
            main_ips = self.resolve_domain(self.domain)
            if main_ips:
                for ip in main_ips:
                    ip_parts = ip.split(".")
                    if len(ip_parts) != 4:
                        continue
                    try:
                        last = int(ip_parts[3])
                    except ValueError:
                        continue
                    base_ip = ".".join(ip_parts[:3])
                    # Scan ±10 neighbours; range end is exclusive so +11 covers last+10
                    for i in range(max(1, last - 10), min(255, last + 11)):
                        try:
                            hostname = socket.gethostbyaddr(f"{base_ip}.{i}")[0].lower()
                            if hostname.endswith(f".{self.domain}") and self.is_valid(hostname):
                                subdomains.add(hostname)
                        except Exception:
                            pass
        except Exception as e:
            print(f"{Fore.RED}[!] Error with reverse DNS: {e}")

        return subdomains
