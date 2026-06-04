import dns.name
from concurrent.futures import ThreadPoolExecutor, as_completed

from colorama import Fore
from tqdm import tqdm
from modules.base import BaseScanner


class DnsBruteforce(BaseScanner):
    name = "DNS Brute Force"
    description = "Wordlist brute force, SRV records, zone transfer"

    def run(self) -> set[str]:
        print(f"{Fore.CYAN}[*] Performing DNS enumeration...")
        subdomains = set()

        wordlist = self.default_wordlist
        if self.wordlist:
            try:
                with open(self.wordlist, "r", encoding="utf-8-sig", errors="ignore") as f:
                    wordlist = [line.strip() for line in f if line.strip()]
            except Exception:
                print(f"{Fore.RED}[!] Could not read wordlist file, using default")

        prefixes = ["dev", "test", "prod", "uat", "new", "old", "staging", "beta", "alpha"]
        suffixes = ["dev", "prod", "test", "api", "app", "web", "mobile"]

        permutations = []
        for word in wordlist:
            permutations.append(word)
            for prefix in prefixes:
                permutations.append(f"{prefix}-{word}")
                permutations.append(f"{prefix}{word}")
            for suffix in suffixes:
                permutations.append(f"{word}-{suffix}")
                permutations.append(f"{word}{suffix}")
            for i in range(1, 10):
                permutations.append(f"{word}{i}")

        permutations = list(set(permutations))

        if not self.wordlist and len(permutations) > 500:
            print(f"{Fore.YELLOW}[!] DNS brute force: capping default permutations at 500 (use --wordlist for full scan)")
            permutations = permutations[:500]

        def check_subdomain(word):
            subdomain = f"{word}.{self.domain}"
            if self.resolve_domain(subdomain):
                return subdomain
            return None

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(check_subdomain, word) for word in permutations]
            with tqdm(total=len(futures), desc="DNS Brute Force") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        subdomains.add(result)
                    pbar.update(1)

        srv_records = ["_sip._tcp", "_sips._tcp", "_jabber._tcp", "_xmpp-server._tcp"]
        for srv in srv_records:
            try:
                resolver = self.get_resolver()
                answers = resolver.resolve(f"{srv}.{self.domain}", "SRV")
                for answer in answers:
                    target = str(answer.target).rstrip(".")
                    if target.endswith(f".{self.domain}"):
                        subdomains.add(target)
            except Exception:
                pass

        try:
            resolver = self.get_resolver()
            ns_answers = resolver.resolve(self.domain, "NS")
            for ns in ns_answers:
                ns_server = str(ns.target).rstrip(".")
                try:
                    zone = dns.zone.from_xfr(dns.query.xfr(ns_server, self.domain))
                    for name in zone.nodes.keys():
                        label = name.to_text().rstrip(".")
                        if label and label != "@":
                            subdomains.add(f"{label}.{self.domain}")
                except Exception:
                    pass
        except Exception:
            pass

        return subdomains
