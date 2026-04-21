import re

from colorama import Fore
from modules.base import BaseScanner


class WhoisXML(BaseScanner):
    name = "WhoisXML"
    description = "WhoisXML Subdomain Lookup API"
    requires_key = "whoisxml"

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Querying WhoisXML Subdomain Lookup API...")
        subdomains = set()

        try:
            url = "https://subdomains.whoisxmlapi.com/api/v1"
            params = {
                "apiKey": self.api_keys["whoisxml"],
                "domainName": self.domain,
                "outputFormat": "json",
            }
            response = self.get_session().get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                total_count = result.get("count", 0)
                records = result.get("records", [])

                for record in records:
                    domain_name = record.get("domain", "")
                    if not domain_name:
                        continue
                    domain_name = re.sub(r'^(\*\.)+', '', domain_name)
                    if domain_name.endswith(f".{self.domain}") and self.is_valid(domain_name):
                        subdomains.add(domain_name)

                print(f"{Fore.GREEN}[+] WhoisXML: {len(subdomains)} valid subdomains from {total_count} total records")
            elif response.status_code == 401:
                print(f"{Fore.RED}[!] WhoisXML API: Invalid or expired API key")
            elif response.status_code == 402:
                print(f"{Fore.RED}[!] WhoisXML API: Out of API credits")
            else:
                print(f"{Fore.RED}[!] WhoisXML API returned status {response.status_code}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error with WhoisXML API: {e}")

        return subdomains
