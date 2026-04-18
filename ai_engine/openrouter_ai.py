"""
OpenRouter AI — subdomain generation via any LLM on OpenRouter.

Drop this file in ai_engine/ and pass --openrouter-key to activate.
Delete to disable. No other changes required.

Default model: anthropic/claude-sonnet-4-5
Override:      --openrouter-model <model-id>
"""

import re
import time

import requests
from colorama import Fore
from ai_engine.base import BaseAIEngine


class OpenRouterAI(BaseAIEngine):
    name = "OpenRouter AI"
    description = "AI-powered subdomain generation via OpenRouter"
    requires_key = "openrouter"

    _DEFAULT_MODEL = "anthropic/claude-sonnet-4-5"
    _BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    # ------------------------------------------------------------------ #

    def run(self):
        print(f"{Fore.CYAN}[*] OpenRouter AI: analyzing patterns and generating subdomains...")
        api_key = self.api_keys["openrouter"]
        model = getattr(self.enumerator, "openrouter_model", self._DEFAULT_MODEL)

        existing = [
            s.replace(f".{self.domain}", "")
            for s in self.subdomains
            if s.endswith(f".{self.domain}")
        ]

        try:
            if len(existing) >= 3:
                raw = self._generate_pattern_based(api_key, model, existing)
                validated = self._validate(api_key, model, raw, existing)
                candidates = validated or raw
                print(
                    f"{Fore.GREEN}[+] OpenRouter AI: {len(raw)} generated → "
                    f"{len(candidates)} validated"
                )
            else:
                candidates = self._generate_basic(api_key, model)
                print(f"{Fore.GREEN}[+] OpenRouter AI: {len(candidates)} candidates (basic mode)")

            return {f"{c}.{self.domain}" for c in candidates if self._ok(c)}

        except Exception as e:
            print(f"{Fore.RED}[!] OpenRouter AI error: {e}")
            return set()

    # ------------------------------------------------------------------ #

    def _generate_basic(self, key, model):
        prompt = (
            f"Generate a focused list of the 30 most common subdomain prefixes for: {self.domain}\n\n"
            "Focus on: web services (www, api, mail), dev environments (dev, staging, test), "
            "admin interfaces (admin, panel), CDN (cdn, static, assets), "
            "support (help, docs, support).\n\n"
            "Provide ONLY a comma-separated list of subdomain prefixes, nothing else.\n"
            "Example: www,api,dev,staging,mail,admin"
        )
        resp = self._call(key, model, prompt, max_tokens=400)
        return self._parse_csv(resp)

    def _generate_pattern_based(self, key, model, existing):
        sample = existing[:15] + existing[-15:] if len(existing) > 30 else existing
        prompt = (
            f"Analyze these discovered subdomains for {self.domain} and generate 30 NEW variations "
            f"that follow the same patterns:\n\n"
            f"DISCOVERED: {', '.join(sample)}\n\n"
            "Look for: numbering schemes, environment patterns (dev/staging/prod), "
            "regional codes, service names, version patterns.\n\n"
            "Provide ONLY a comma-separated list of NEW subdomain prefixes, no duplicates, no explanations."
        )
        resp = self._call(key, model, prompt, max_tokens=600)
        found = self._parse_csv(resp)
        return found - set(existing)

    def _validate(self, key, model, candidates, existing):
        if not candidates:
            return set()
        top = list(candidates)[:20]
        prompt = (
            f"From this list of subdomain candidates for {self.domain}, "
            f"select the 10 most likely to actually exist based on these existing subdomains:\n\n"
            f"EXISTING: {', '.join(existing[:15])}\n"
            f"CANDIDATES: {', '.join(top)}\n\n"
            "Return ONLY a comma-separated list of the top 10 candidates."
        )
        resp = self._call(key, model, prompt, max_tokens=300)
        ranked = self._parse_csv(resp)
        return ranked & candidates if ranked else candidates

    # ------------------------------------------------------------------ #

    def _call(self, key, model, prompt, max_tokens=600):
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/bidhata/SubGrab",
            "X-Title": "SubGrab Subdomain Discovery",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity expert specializing in subdomain enumeration. "
                        "Provide only the requested lists with no explanations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        for attempt in range(3):
            try:
                r = requests.post(self._BASE_URL, headers=headers, json=payload, timeout=60)
                if r.status_code in (429, 502, 503, 504) and attempt < 2:
                    time.sleep(3 * (2 ** attempt))
                    continue
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3 * (2 ** attempt))
        return ""

    def _parse_csv(self, text):
        out = set()
        if not text:
            return out
        for line in text.split("\n"):
            if "," in line and not line.strip().startswith("#"):
                for part in line.split(","):
                    s = re.sub(r"[^a-zA-Z0-9\-]", "", part.strip().lower())
                    if s and 2 <= len(s) <= 63:
                        out.add(s)
        return out

    def _ok(self, label):
        return bool(re.match(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$", label))
