from __future__ import annotations
from colorama import Fore
from modules.base import BaseScanner


class SecurityAPIs(BaseScanner):
    name = "Security APIs"
    description = "VirusTotal, SecurityTrails, Censys, Shodan"

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Querying security APIs...")
        subdomains = set()

        if "virustotal" in self.api_keys:
            try:
                headers = {"x-apikey": self.api_keys["virustotal"]}
                url = f"https://www.virustotal.com/api/v3/domains/{self.domain}/subdomains"
                cursor = None
                # Cap at 50 pages × 40/page = 2000 subdomains. Large orgs (Microsoft,
                # Ericsson, etc.) routinely have more, but VT's free tier rate-limits
                # heavily so 50 pages is a reasonable upper bound.
                for _ in range(50):
                    params = {"limit": 40}
                    if cursor:
                        params["cursor"] = cursor
                    response = self.get_session().get(url, headers=headers, params=params, timeout=30)
                    if response.status_code == 429:
                        print(f"{Fore.YELLOW}[!] VirusTotal rate limit reached (429). Skipping remaining pages.")
                        break
                    elif response.status_code != 200:
                        print(f"{Fore.RED}[!] VirusTotal returned HTTP {response.status_code}")
                        break
                    data = response.json()
                    for item in data.get("data", []):
                        name = item.get("id", "")
                        if name.endswith(f".{self.domain}"):
                            subdomains.add(name)
                    cursor = data.get("meta", {}).get("cursor")
                    if not cursor:
                        break
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
                censys_auth = self.api_keys["censys"]
                if "pat" in censys_auth:
                    # Platform API v3 using Personal Access Token
                    url = "https://api.platform.censys.io/v3/global/search/query"
                    headers = {
                        "Authorization": f"Bearer {censys_auth['pat']}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    payload = {"query": f"names: *.{self.domain}", "per_page": 100}
                    response = self.get_session().post(url, headers=headers, json=payload, timeout=30)
                else:
                    # Legacy Search API v2 using Basic Auth
                    url = "https://search.censys.io/api/v2/certificates/search"
                    auth = (censys_auth["id"], censys_auth["secret"])
                    params = {"q": f"names: *.{self.domain}", "per_page": 100}
                    response = self.get_session().get(url, auth=auth, params=params, timeout=30)
                    
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("result", {}).get("hits", [])
                    if not hits and "results" in data:
                        hits = data.get("results", [])
                        
                    for result in hits:
                        # Censys v2/v3 may place names under 'parsed'
                        names = result.get("names", [])
                        if not names and "parsed" in result:
                            names = result["parsed"].get("names", [])
                            
                        for name in names:
                            if name.endswith(f".{self.domain}"):
                                subdomains.add(name)
                elif response.status_code == 401:
                    print(f"{Fore.RED}[!] Censys API: Invalid API ID or Secret (401 Unauthorized)")
                elif response.status_code == 403:
                    print(f"{Fore.RED}[!] Censys API: Access Denied / Out of Credits (403 Forbidden)")
                elif response.status_code == 429:
                    print(f"{Fore.YELLOW}[!] Censys API: Rate limit exceeded (429 Too Many Requests)")
                else:
                    print(f"{Fore.RED}[!] Censys API returned HTTP {response.status_code}: {response.text[:100]}")
            except Exception as e:
                print(f"{Fore.RED}[!] Error with Censys: {e}")

        if "shodan" in self.api_keys:
            try:
                shodan_domains = self.shodan_scan()
                subdomains.update(shodan_domains)
            except Exception as e:
                print(f"{Fore.RED}[!] Error with Shodan scan: {e}")

        return subdomains
