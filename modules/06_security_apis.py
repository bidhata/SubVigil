from colorama import Fore
from modules.base import BaseScanner


class SecurityAPIs(BaseScanner):
    name = "Security APIs"
    description = "VirusTotal, SecurityTrails, Censys, Shodan"

    def run(self):
        print(f"{Fore.CYAN}[*] Querying security APIs...")
        subdomains = set()

        if "virustotal" in self.api_keys:
            try:
                url = "https://www.virustotal.com/vtapi/v2/domain/report"
                params = {"apikey": self.api_keys["virustotal"], "domain": self.domain}
                response = self.get_session().get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for subdomain in data.get("subdomains", []):
                        if subdomain.endswith(f".{self.domain}"):
                            subdomains.add(subdomain)
            except Exception as e:
                print(f"{Fore.RED}[!] Error with VirusTotal: {e}")

        if "securitytrails" in self.api_keys:
            try:
                url = f"https://api.securitytrails.com/v1/domain/{self.domain}/subdomains"
                headers = {"APIKEY": self.api_keys["securitytrails"]}
                response = self.get_session().get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for subdomain in data.get("subdomains", []):
                        subdomains.add(f"{subdomain}.{self.domain}")
            except Exception as e:
                print(f"{Fore.RED}[!] Error with SecurityTrails: {e}")

        if "censys" in self.api_keys:
            try:
                url = "https://search.censys.io/api/v2/certificates/search"
                auth = (self.api_keys["censys"]["id"], self.api_keys["censys"]["secret"])
                params = {"q": f"names: *.{self.domain}", "per_page": 100}
                response = self.get_session().get(url, auth=auth, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("result", {}).get("hits", []):
                        for name in result.get("names", []):
                            if name.endswith(f".{self.domain}"):
                                subdomains.add(name)
            except Exception as e:
                print(f"{Fore.RED}[!] Error with Censys: {e}")

        if "shodan" in self.api_keys:
            try:
                shodan_domains = self.shodan_scan()
                subdomains.update(shodan_domains)
            except Exception as e:
                print(f"{Fore.RED}[!] Error with Shodan scan: {e}")

        return subdomains
