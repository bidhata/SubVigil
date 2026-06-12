# ai_engine/_binary_base.py
import re
import shutil
import subprocess

from colorama import Fore

from ai_engine.base import BaseAIEngine


class BinaryAIEngine(BaseAIEngine):
    """Base class for AI engines that invoke a local CLI binary via subprocess."""

    binary: str = ""
    binary_args: tuple = ()

    def run(self):
        binary_path = shutil.which(self.binary)
        if not binary_path:
            print(f"{Fore.YELLOW}[~] {self.name}: binary '{self.binary}' not found, skipping.")
            return set()

        prompt = self._build_prompt()
        cmd = self._build_cmd(binary_path)

        print(f"{Fore.CYAN}[*] {self.name}: generating subdomains via {self.binary}...")

        try:
            result = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=120
            )
            labels = self._parse_lines(result.stdout)
            
            if result.returncode != 0 and not labels:
                print(
                    f"{Fore.RED}[!] {self.name}: exited with code {result.returncode}: "
                    f"\n... {result.stderr.strip()[-1000:]}"
                )
                return set()
                
            return {
                f"{label}.{self.domain}"
                for label in labels
                if self.is_valid(f"{label}.{self.domain}")
            }
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}[!] {self.name}: timed out after 120s")
            return set()
        except Exception as e:
            print(f"{Fore.RED}[!] {self.name} error: {e}")
            return set()

    def _build_cmd(self, binary_path):
        cmd = [binary_path, *self.binary_args, "-"]
        if binary_path.upper().endswith(".CMD"):
            cmd = ["cmd", "/c"] + cmd
        return cmd

    def _build_prompt(self):
        existing = [
            s.replace(f".{self.domain}", "")
            for s in self.subdomains
            if s.endswith(f".{self.domain}")
        ]
        
        # Cap to 1000 to prevent LLM context window limits and IPC buffer issues
        if len(existing) > 100:
            existing = existing[:100]
            
        if len(existing) >= 3:
            label_block = "\n".join(existing)
            return (
                f"The target domain is {self.domain}.\n"
                f"These subdomains have already been discovered:\n{label_block}\n\n"
                "Based on these patterns, suggest 25 more subdomain labels that would "
                "commonly exist for this organisation.\n"
                "Output one subdomain label per line. No explanation. No punctuation. Labels only."
            )
        return (
            f"Generate 30 common subdomain labels for the domain: {self.domain}\n\n"
            "Include: dev environments (dev, staging, qa, uat), APIs (api, rest, graphql), "
            "services (mail, vpn, auth, sso), CDN (cdn, static, assets), "
            "admin (admin, portal, dashboard).\n\n"
            "Output one subdomain label per line. No explanation. No punctuation. Labels only."
        )

    def _parse_lines(self, text):
        out = set()
        for line in text.strip().split("\n"):
            label = line.strip().lower()
            if len(label) >= 2 and re.match(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$", label):
                out.add(label)
        return out
