# ─────────────────────────────────────────────────────────────────────────────
# SubGrab AI Engine Plugin Template
#
# HOW TO USE:
#   1. Copy this file, rename it  e.g. my_llm.py
#   2. Fill in name, description, requires_key, and the run() method
#   3. Drop the file in this folder — it loads automatically next scan
#   4. Delete the file to disable it — nothing else to change
#
# BaseAIEngine and Fore are pre-injected — no imports needed for those.
# Add any other imports you need at the top of your file as normal.
#
# AI engines run AFTER passive scanners, so self.subdomains already
# contains all passively discovered subdomains when run() is called.
# Use them to guide pattern-based generation.
# ─────────────────────────────────────────────────────────────────────────────


class MyLLM(BaseAIEngine):              # BaseAIEngine is pre-injected — no import needed
    name         = "My LLM"            # shown in logs and startup list
    description  = "One-line description of what this AI engine does"
    requires_key = "my_llm"            # key in api_keys dict; engine auto-skipped when absent

    fast_mode_skip = False             # set True to skip when --fast flag is passed

    def run(self):
        """Return a set of discovered subdomain strings."""
        subdomains = set()
        api_key = self.api_keys[self.requires_key]

        # Build context from already-discovered subdomains
        existing = [
            s.replace(f".{self.domain}", "")
            for s in self.subdomains
            if s.endswith(f".{self.domain}")
        ]

        try:
            # Example: call your LLM API and parse generated subdomain labels
            labels = self._call_llm(api_key, existing)
            for label in labels:
                full = f"{label}.{self.domain}"
                if self.is_valid(full):
                    subdomains.add(full)

        except Exception as e:
            print(f"{Fore.RED}[!] {self.name} error: {e}")

        return subdomains

    def _call_llm(self, api_key, existing):
        """Call your LLM and return an iterable of subdomain label strings."""
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# QUICK REFERENCE — everything available inside run()
#
#   self.domain            target domain string  (e.g. "example.com")
#   self.api_keys          dict of configured API keys
#   self.subdomains        ALL subdomains found by passive scanners (read-only)
#   self.subdomain_info    per-subdomain metadata dict
#   self.output_dir        path to the results directory
#   self.fast_mode         True when --fast was passed
#   self.threads           thread count
#   self.timeout           HTTP/DNS timeout in seconds
#
#   self.get_session()               thread-local requests.Session
#   self.get_resolver()              thread-local dns.resolver.Resolver
#   self.resolve_domain(sub)         → list[str] IPs  or  None
#   self.is_valid(sub)               → bool  (format + domain check)
#
#   Fore.RED / GREEN / CYAN / YELLOW / RESET   (colorama, pre-injected)
# ─────────────────────────────────────────────────────────────────────────────
