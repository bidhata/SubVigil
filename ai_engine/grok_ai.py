"""
Grok AI — subdomain generation via xAI's Grok models.

Drop this file in ai_engine/ and pass --grok-key to activate.
Delete to disable. No other changes required.

Default model: grok-3
Override:      --grok-model <model-id>   (grok-3-fast, grok-3-mini, grok-3-mini-fast)
"""

import re
import time

import requests
from colorama import Fore
from ai_engine.base import BaseAIEngine


class GrokAI(BaseAIEngine):
    name = "Grok AI"
    description = "AI-powered subdomain generation via Grok (xAI)"
    requires_key = "grok"

    _DEFAULT_MODEL = "grok-3"
    _BASE_URL = "https://api.x.ai/v1/chat/completions"

    # ------------------------------------------------------------------ #

    def run(self):
        print(f"{Fore.CYAN}[*] Grok AI: analyzing patterns and generating subdomains...")
        api_key = self.api_keys["grok"]
        model = getattr(self.enumerator, "grok_model", self._DEFAULT_MODEL)

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
                    f"{Fore.GREEN}[+] Grok AI: {len(raw)} generated → "
                    f"{len(candidates)} validated"
                )
            else:
                candidates = self._generate_basic(api_key, model)
                print(f"{Fore.GREEN}[+] Grok AI: {len(candidates)} candidates (basic mode)")

            return {f"{c}.{self.domain}" for c in candidates if self._ok(c)}

        except Exception as e:
            print(f"{Fore.RED}[!] Grok AI error: {e}")
            return set()

    # ------------------------------------------------------------------ #

    def _generate_basic(self, key, model):
        prompt = (
            f"Generate 30 likely subdomain prefixes for: {self.domain}\n\n"
            "Include: dev environments (dev, test, staging, qa, uat), "
            "APIs (api, api-v1, rest, graphql), services (mail, vpn, auth, sso), "
            "CDN (cdn, static, assets, media), docs (docs, help, wiki).\n\n"
            "Output ONLY subdomain prefixes, one per line, no explanations."
        )
        resp = self._call(key, model, prompt, max_tokens=400)
        return self._parse_lines(resp)

    def _generate_pattern_based(self, key, model, existing):
        sample = existing[:50]
        prompt = (
            f"Analyze these discovered subdomains for {self.domain} and generate "
            f"25 additional likely subdomains based on the patterns:\n\n"
            f"{chr(10).join(sample)}\n\n"
            "Look for: numbering schemes, environment patterns, regional codes, "
            "service names, version patterns, department names.\n\n"
            "Output ONLY new subdomain prefixes, one per line, no duplicates, no explanations."
        )
        resp = self._call(key, model, prompt, max_tokens=500)
        found = self._parse_lines(resp)
        return found - set(existing)

    def _validate(self, key, model, candidates, existing):
        if not candidates or len(candidates) <= 30:
            return {c for c in candidates if self._ok(c)}
        top = list(candidates)[:50]
        prompt = (
            f"Rank these subdomain candidates for {self.domain} by likelihood of existence.\n\n"
            f"Existing (for context):\n{chr(10).join(existing[:20])}\n\n"
            f"Candidates:\n{chr(10).join(top)}\n\n"
            "Select the 30 MOST LIKELY candidates. "
            "Output ONLY subdomain names, one per line, no explanations."
        )
        resp = self._call(key, model, prompt, max_tokens=400)
        ranked = self._parse_lines(resp)
        valid = ranked & candidates
        return valid if len(valid) >= 10 else {c for c in candidates if self._ok(c)}

    # ------------------------------------------------------------------ #

    def _call(self, key, model, prompt, max_tokens=500):
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert cybersecurity researcher specializing in "
                        "subdomain enumeration. Respond only with the requested list."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False,
        }
        for attempt in range(3):
            try:
                r = requests.post(self._BASE_URL, headers=headers, json=payload, timeout=60)
                if r.status_code in (429, 502, 503, 504) and attempt < 2:
                    time.sleep(3 * (2 ** attempt))
                    continue
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:120]}")
            except RuntimeError:
                raise
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3 * (2 ** attempt))
        return ""

    def _parse_lines(self, text):
        out = set()
        if not text:
            return out
        for line in text.strip().split("\n"):
            s = line.strip().strip("-").strip(".").strip("*").lower()
            s = re.sub(r"[^a-z0-9\-]", "", s)
            if s and 2 <= len(s) <= 63:
                out.add(s)
        return out

    def _ok(self, label):
        return bool(re.match(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$", label))
