# SubGrab — Advanced Subdomain Enumeration Tool

**Python 3.8+** | **MIT License** | **Windows / Linux / macOS**

SubGrab is a high-performance, multi-threaded subdomain enumeration tool designed for security researchers, penetration testers, and bug bounty hunters. It combines 11 modular passive discovery sources, active reconnaissance, and optional AI-powered pattern generation (Grok / OpenRouter) into a single CLI and GUI tool.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [CLI Reference](#cli-reference)
6. [Passive Scanner Modules](#passive-scanner-modules)
7. [Active Reconnaissance](#active-reconnaissance)
8. [API Integrations](#api-integrations)
9. [AI Integration](#ai-integration)
10. [Output Formats](#output-formats)
11. [Adding a New Scanner Module](#adding-a-new-scanner-module)
12. [GUI Interface](#gui-interface)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)
15. [License](#license)

---

## Features

### Passive Discovery
- Certificate Transparency logs (crt.sh + CertSpotter)
- Web archives (Wayback Machine + CommonCrawl — always uses latest index)
- Search engine dorks (Google site:/inurl:)
- C99 SubdomainFinder scan retrieval with three-tier HTML parsing fallback
- DNS databases: DNSdumpster, HackerTarget
- WhoisXML Subdomain Lookup API (500 free credits)
- Security APIs: VirusTotal, SecurityTrails, Censys, Shodan
- GitHub code search for domain leaks
- DNS brute force with permutation expansion, SRV records, zone transfer
- Reverse DNS sweeping across discovered IP ranges
- AI-powered generation: Grok (xAI) and/or OpenRouter models

### Active Reconnaissance
- HTTP/HTTPS status code probing and technology fingerprinting
- SSH port detection (port 22)
- Port scanning for common services (HTTP, HTTPS, FTP, SMTP)
- IP owner lookup via Shodan
- Subdomain takeover detection across 50+ cloud/SaaS services

### Analysis & Output
- Wildcard DNS detection (eliminates false positives before scanning)
- Subdomain takeover detection across AWS S3, Azure, GitHub Pages, Heroku, Netlify, Vercel, and 45+ more
- Results in TXT, CSV, JSON, and interactive HTML with charts
- Real-time progress bars via tqdm

---

## Architecture

SubGrab uses a **plugin-based module system** for passive discovery. Each scanner lives in its own file under `modules/` and is auto-discovered at runtime — no registration required.

```
SubGrab-main/
├── subgrab.py              # Main CLI entry point + SubdomainEnumerator class
├── subgrab_gui.py          # Tkinter GUI wrapper
├── openrouter_integration.py   # OpenRouter AI enhancer
├── grok_integration.py         # Grok (xAI) AI enhancer
├── requirements.txt
├── start_subgrab_gui.bat   # Windows one-click launcher
└── modules/
    ├── base.py                          # BaseScanner ABC + load_modules()
    ├── 01_certificate_transparency.py
    ├── 02_web_archives.py
    ├── 03_search_engines.py
    ├── 04_dns_databases.py
    ├── 05_whoisxml.py
    ├── 06_security_apis.py
    ├── 07_github_search.py
    ├── 08_dns_bruteforce.py
    ├── 09_reverse_dns.py
    ├── 10_openrouter_ai.py
    └── 11_grok_ai.py
```

`SubdomainEnumerator.run_passive_discovery()` calls `load_modules()`, which sorts `modules/*.py` alphabetically and instantiates every `BaseScanner` subclass it finds. The numeric prefix controls execution order.

---

## Installation

**Requirements:** Python 3.8+

```bash
git clone https://github.com/bidhata/SubGrab.git
cd SubGrab
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client |
| `dnspython` | DNS resolution, zone transfer, SRV |
| `colorama` | Coloured terminal output |
| `beautifulsoup4` | HTML parsing (C99 scan pages) |
| `lxml` | Fast HTML parser (fallback: html.parser) |
| `tqdm` | Progress bars |
| `shodan` | Shodan API client |
| `urllib3`, `certifi` | TLS/SSL support |

---

## Quick Start

```bash
# Passive-only scan (no API keys required)
python subgrab.py example.com

# Fast mode: skips DNS brute force and reverse DNS
python subgrab.py example.com --fast --threads 100

# Stealth mode: random delays between requests
python subgrab.py example.com --stealth

# With Grok AI pattern generation (recommended free option)
python subgrab.py example.com --grok-key xai-YOURKEY

# With OpenRouter AI (Claude, GPT-4o, Gemini, etc.)
python subgrab.py example.com --openrouter-key sk-or-YOURKEY --openrouter-model anthropic/claude-3.5-sonnet

# Dual AI + Shodan + VirusTotal — maximum coverage
python subgrab.py example.com \
  --grok-key xai-YOURKEY \
  --openrouter-key sk-or-YOURKEY \
  --shodan-key SHODANKEY \
  --virustotal-key VTKEY \
  --threads 100

# Launch GUI
python subgrab_gui.py
```

---

## CLI Reference

```
usage: subgrab.py [-h] [-t THREADS] [--timeout TIMEOUT] [--fast] [--stealth]
                  [--proxy-file FILE] [--wordlist FILE] [--nameservers NS [NS ...]]
                  [--shodan-key KEY] [--securitytrails-key KEY]
                  [--virustotal-key KEY] [--censys-id ID] [--censys-secret SECRET]
                  [--github-token TOKEN] [--whoisxml-key KEY]
                  [--openrouter-key KEY] [--openrouter-model MODEL]
                  [--grok-key KEY] [--grok-model MODEL]
                  domain
```

### Positional

| Argument | Description |
|----------|-------------|
| `domain` | Target domain (e.g. `example.com`) |

### General Options

| Flag | Default | Description |
|------|---------|-------------|
| `-t, --threads` | `50` | Worker thread count (1–200) |
| `--timeout` | `30` | HTTP/DNS request timeout in seconds |
| `--fast` | off | Skip DNS brute force and reverse DNS (faster but less thorough) |
| `--stealth` | off | Add 0.5–2.0s random delays between requests |
| `--proxy-file FILE` | — | Path to newline-separated proxy list |
| `--wordlist FILE` | built-in | Custom wordlist for DNS brute force |
| `--nameservers NS...` | `8.8.8.8 8.8.4.4 1.1.1.1` | DNS resolvers to use |

### API Keys

| Flag | Service | Free Tier |
|------|---------|-----------|
| `--shodan-key KEY` | Shodan | Limited |
| `--securitytrails-key KEY` | SecurityTrails | 50 req/month |
| `--virustotal-key KEY` | VirusTotal | 4 req/min |
| `--censys-id ID` + `--censys-secret SECRET` | Censys | 250 req/month |
| `--github-token TOKEN` | GitHub | 5,000 req/hour |
| `--whoisxml-key KEY` | WhoisXML | 500 credits |

### AI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--grok-key KEY` | — | xAI Grok API key |
| `--grok-model MODEL` | `grok-3` | Grok model to use |
| `--openrouter-key KEY` | — | OpenRouter API key |
| `--openrouter-model MODEL` | `anthropic/claude-3.5-sonnet` | OpenRouter model |

### Persistent API Key Configuration

Store keys in `api_keys.json` at the project root so you don't have to pass them on every run (this file is `.gitignore`d):

```json
{
  "grok": "xai-YOURKEY",
  "openrouter": "sk-or-YOURKEY",
  "shodan": "YOURKEY",
  "virustotal": "YOURKEY",
  "securitytrails": "YOURKEY",
  "censys": {
    "id": "YOURKEY",
    "secret": "YOURSECRET"
  },
  "github": "YOURTOKEN",
  "whoisxml": "YOURKEY"
}
```

The GUI's **API Keys** tab loads and saves this file directly.

---

## Passive Scanner Modules

All modules live in `modules/` and inherit from `BaseScanner`. They are executed in filename order.

| # | File | Class | Description | API Key Required | Fast-skip |
|---|------|-------|-------------|-----------------|-----------|
| 01 | `01_certificate_transparency.py` | `CertificateTransparency` | crt.sh (retry+backoff) · CertSpotter · Entrust CT · tls.bufferover.run · urlscan.io | — | No |
| 02 | `02_web_archives.py` | `WebArchives` | Wayback Machine CDX + CommonCrawl (latest index auto-detected) | — | No |
| 03 | `03_search_engines.py` | `SearchEngines` | Bing (paginated) · DuckDuckGo HTML · Yahoo · Google fallback | — | No |
| 04 | `04_dns_databases.py` | `DnsDatabases` | C99 SubdomainFinder → DNSdumpster → HackerTarget (first with results wins) | — | No |
| 05 | `05_whoisxml.py` | `WhoisXML` | WhoisXML Subdomain Lookup API | `whoisxml` | No |
| 06 | `06_security_apis.py` | `SecurityAPIs` | VirusTotal, SecurityTrails, Censys, Shodan | optional per-API | No |
| 07 | `07_github_search.py` | `GitHubSearch` | GitHub REST API (text-match header) + HTML scrape fallback | optional `github` | **Yes** |
| 08 | `08_dns_bruteforce.py` | `DnsBruteforce` | Wordlist + permutations brute force, SRV records, zone transfer | — | No |
| 09 | `09_reverse_dns.py` | `ReverseDNS` | Reverse DNS on ±10 IPs around each discovered address | — | **Yes** |
| 10 | `10_openrouter_ai.py` | `OpenRouterAI` | Pattern-based subdomain generation via OpenRouter LLMs | — (key via CLI) | No |
| 11 | `11_grok_ai.py` | `GrokAI` | Pattern-based subdomain generation via xAI Grok | — (key via CLI) | No |

**Fast-skip** modules (07, 09) are silently bypassed when `--fast` is passed.  
**API-gated** modules (05, 06 sub-features) are skipped if the required key is absent.

### C99 Subdomain Finder — Parsing Resilience

The C99 scanner uses a three-tier fallback to handle HTML layout changes:

1. Parse `class="sd"` elements (original layout)
2. Try alternative class names: `subdomain`, `host`, `domain`, `sub`, `name`
3. Regex sweep over raw HTML: `[\w][\w\-]*(?:\.[\w\-]+)*\.{domain}`

When C99 results are found, IP addresses and Cloudflare status are also extracted and saved to `{domain}_c99_scan.json`.

### DNS Brute Force — Permutation Expansion

For each word in the wordlist, `08_dns_bruteforce.py` generates:
- Raw word
- `{prefix}-{word}` and `{prefix}{word}` for prefixes: `dev test prod uat new old staging beta alpha`
- `{word}-{suffix}` and `{word}{suffix}` for suffixes: `dev prod test api app web mobile`
- `{word}1` through `{word}9`

All permutations are deduplicated and resolved in parallel via `ThreadPoolExecutor`.

---

## Active Reconnaissance

After passive discovery, `active_reconnaissance()` probes every found subdomain in parallel:

- **HTTP/HTTPS probing**: status code, redirect chain, `Server` header, page title
- **Port scanning**: 22 (SSH), 80 (HTTP), 443 (HTTPS), 21 (FTP), 25 (SMTP)
- **Technology detection**: server banner, common framework patterns
- **Shodan enrichment**: IP owner, open ports, CVEs (requires Shodan key + active subdomains)
- **Takeover detection**: DNS CNAME resolution + HTTP body matching against 50+ service fingerprints

Subdomain takeover coverage includes: AWS S3, Azure (Blob/App Service/CDN/Traffic Manager), GitHub Pages, Heroku, Netlify, Vercel, Fly.io, Render, Firebase, Fastly, Cloudfront, Surge.sh, Ghost, Zendesk, HelpJuice, Freshdesk, UserVoice, Intercom, Tumblr, WordPress.com, and more.

---

## API Integrations

### Free Sources (no key needed)

| Source | Method | Typical yield |
|--------|--------|--------------|
| crt.sh | CT JSON API — 3× retry with exponential backoff on rate-limit | High |
| CertSpotter | CT issuance API | Medium |
| Entrust CT Search | CT certificate subjectDN API | Medium |
| tls.bufferover.run | TLS/forward-DNS dataset | Medium |
| urlscan.io | Page domain index (1,000 results) | Medium |
| Wayback Machine | CDX search API | Medium |
| CommonCrawl | Index search API (latest index auto-fetched) | Medium |
| Bing | Site dorks, paginated (10 pages) | Medium |
| DuckDuckGo | HTML endpoint site dorks | Low–Medium |
| Yahoo | Site dorks, paginated | Low–Medium |
| Google | Site/inurl dorks (fallback — often blocked) | Low |
| HackerTarget | hostsearch API | Medium |
| DNSdumpster | Common-prefix DNS resolution | Low |
| GitHub | REST API text-match + HTML scrape fallback | Low |

### Key-Gated Sources

| Service | Key Flag | Free Tier | Notes |
|---------|----------|-----------|-------|
| WhoisXML | `--whoisxml-key` | 500 credits | Subdomain lookup API |
| VirusTotal | `--virustotal-key` | 4 req/min | Domain report |
| SecurityTrails | `--securitytrails-key` | 50 req/month | Subdomain list |
| Censys | `--censys-id` + `--censys-secret` | 250 req/month | Certificate search |
| GitHub | `--github-token` | 5,000 req/hr | Code search (optional) |
| Shodan | `--shodan-key` | Limited | Active IP scan only |

---

## AI Integration

AI modules activate **after** all traditional passive sources have run, so the AI analyzes real discovered patterns rather than guessing blindly.

### Workflow

1. Traditional modules collect initial subdomains (e.g. `api`, `api1`, `dev-api`)
2. AI receives the label list (domain suffix stripped)
3. If ≥ 3 labels found → **pattern analysis mode**: AI generates candidates based on observed conventions
4. If < 3 labels → **basic generation mode**: AI falls back to common industry patterns
5. Generated candidates are validated for format then added to the main set

### Grok (xAI) — Recommended Free Option

Get a key at [console.x.ai](https://console.x.ai). Free credits available for new accounts.

```bash
python subgrab.py example.com --grok-key xai-YOURKEY
python subgrab.py example.com --grok-key xai-YOURKEY --grok-model grok-3-mini
```

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| `grok-3` | General use — **recommended** | Fast | $ |
| `grok-3-mini` | Quick/budget scans | Very fast | ¢ |
| `grok-4` | Complex patterns | Moderate | $$ |
| `grok-4.1-fast` | Large scans (2M context) | Fast | $ |

**Typical cost:** $0.01–$0.50 per scan depending on subdomain count.

### OpenRouter

Access Claude, GPT-4o, Gemini, Llama and others through a single API. Sign up at [openrouter.ai](https://openrouter.ai) and add $5–10 credits.

```bash
python subgrab.py example.com \
  --openrouter-key sk-or-YOURKEY \
  --openrouter-model anthropic/claude-3.5-sonnet
```

| Model | Quality | Cost |
|-------|---------|------|
| `anthropic/claude-3.5-sonnet` | Best overall | $$$ |
| `anthropic/claude-3-haiku` | Fast, affordable | $ |
| `openai/gpt-4o` | High quality | $$$$ |
| `openai/gpt-4o-mini` | Balanced | $$ |
| `google/gemini-pro-1.5` | Good alternative | $$ |
| `meta-llama/llama-3.1-8b-instruct` | Open source, cheap | ¢ |

### Dual AI Mode

Use both simultaneously for independent cross-validation:

```bash
python subgrab.py example.com \
  --grok-key xai-YOURKEY \
  --openrouter-key sk-or-YOURKEY \
  --openrouter-model anthropic/claude-3.5-sonnet
```

### Choosing an AI Strategy

| Your situation | Recommendation |
|----------------|---------------|
| First time / no budget | Grok (free credits) |
| Bug bounty — regular scans | Grok only |
| Pentest engagement | Dual AI (Grok + Claude) |
| Quick recon | `--fast`, no AI |
| Maximum coverage | Dual AI + all API keys |

---

## Output Formats

All results are written to `{domain}_results/`:

```
example.com_results/
├── all_subdomains.txt          # Full deduplicated list
├── active_subdomains.txt       # HTTP/HTTPS responsive subdomains
├── inactive_subdomains.txt     # Non-responsive subdomains
├── ssh_enabled.txt             # Subdomains with port 22 open
├── takeover_candidates.txt     # Potential takeover targets with reason
├── scan_results.json           # Full structured report
├── scan_results.csv            # Spreadsheet-compatible
├── report.html                 # Interactive dashboard with charts
└── {domain}_c99_scan.json      # C99 IP/Cloudflare data (if found)
```

### JSON Report Schema

```json
{
  "domain": "example.com",
  "scan_date": "2026-04-18T12:00:00",
  "total_subdomains": 312,
  "active_subdomains": 187,
  "inactive_subdomains": 125,
  "ssh_enabled": 3,
  "takeover_candidates": 2,
  "subdomains": {
    "api.example.com": {
      "ip": "93.184.216.34",
      "active": true,
      "status_code": 200,
      "server": "nginx",
      "title": "API Gateway",
      "source": "c99"
    }
  }
}
```

---

## Adding a New Scanner Module

The plugin system is fully automatic — **no registration, no config changes**.

| Action | What to do |
|--------|-----------|
| **Add** a scanner | Drop a `.py` file in `modules/` → active on next run |
| **Remove** a scanner | Delete the file → gone on next run |
| **Disable temporarily** | Rename to `_myfile.py` (leading `_` skips it) |
| **Control order** | Prefix with two-digit number: `12_mysource.py` |

On every run the loader prints which plugins it found:
```
[*] Loaded 11 scanner plugin(s): Certificate Transparency, Web Archives, ...
```

### Zero-Import Template

`BaseScanner` and `Fore` are **pre-injected** into every plugin's namespace — no imports needed. Copy `modules/_TEMPLATE.py`, rename it, and fill in `name` and `run()`:

```python
# modules/12_my_source.py  — no imports required

class MySource(BaseScanner):
    name         = "My Source"
    description  = "One-line description shown in logs"

    # optional — scanner is auto-skipped when key is absent:
    requires_key   = None      # e.g. "shodan"

    # optional — skip when --fast flag is passed:
    fast_mode_skip = False

    def run(self):
        subdomains = set()
        try:
            resp = self.get_session().get(
                f"https://api.example.com/subdomains?q={self.domain}",
                timeout=10,
            )
            for entry in resp.json():
                host = entry.get("hostname", "").strip().lower()
                if host.endswith(f".{self.domain}") and self.is_valid(host):
                    subdomains.add(host)
        except Exception as e:
            print(f"{Fore.RED}[!] {self.name} error: {e}")
        return subdomains
```

That's the complete file. No imports, no boilerplate, no registration anywhere.

### How Pre-injection Works

`load_modules()` in `modules/base.py` injects `BaseScanner` and `Fore` into each plugin module's namespace *before* executing it. Existing plugins that already import them explicitly continue to work — the injected names are simply overwritten by the import.

### BaseScanner — Available Inside `run()`

| Member | Type | Description |
|--------|------|-------------|
| `self.domain` | `str` | Target domain |
| `self.api_keys` | `dict` | All configured API keys |
| `self.subdomains` | `set` | Subdomains found so far by earlier modules |
| `self.subdomain_info` | `dict` | Per-subdomain metadata dict |
| `self.output_dir` | `str` | Path to results directory |
| `self.fast_mode` | `bool` | `True` when `--fast` was passed |
| `self.threads` | `int` | Thread count |
| `self.timeout` | `int` | Request timeout in seconds |
| `self.wordlist` | `str\|None` | Custom wordlist path |
| `self.default_wordlist` | `list` | Built-in wordlist |
| `self.get_session()` | method | Thread-local `requests.Session` |
| `self.get_resolver()` | method | Thread-local `dns.resolver.Resolver` |
| `self.resolve_domain(sub)` | method | Resolve subdomain → `list[str]` IPs or `None` |
| `self.is_valid(sub)` | method | Validate subdomain format → `bool` |
| `self.stealth_delay()` | method | Sleep 0.5–2s when `--stealth` is on |
| `self.shodan_scan()` | method | Run Shodan scan on active IPs (needs key) |
| `self.extract_from_json(data)` | method | Extract subdomains from arbitrary JSON |
| `self.extract_from_page(soup, text)` | method | Extract subdomains from BeautifulSoup + text |
| `Fore.RED/GREEN/CYAN/YELLOW` | colorama | Pre-injected color constants for `print()` |

### `requires_key` and `fast_mode_skip`

```python
# Skip this scanner unless --whoisxml-key was provided
requires_key = "whoisxml"

# Skip this scanner when --fast is passed
fast_mode_skip = True
```

The runner checks both flags before instantiating the class — your `run()` method is never called if the condition isn't met. You don't need to check inside `run()`.

### Real Example — adding AlienVault OTX in 15 lines

```python
# modules/12_alienvault.py

class AlienVault(BaseScanner):
    name        = "AlienVault OTX"
    description = "Passive DNS from OTX"

    def run(self):
        subdomains = set()
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns"
            data = self.get_session().get(url, timeout=15).json()
            for record in data.get("passive_dns", []):
                host = record.get("hostname", "").lower().strip()
                if host.endswith(f".{self.domain}") and self.is_valid(host):
                    subdomains.add(host)
        except Exception as e:
            print(f"{Fore.RED}[!] {self.name}: {e}")
        return subdomains
```

Drop `12_alienvault.py` in `modules/` → appears in the next scan's plugin list automatically.

---

## GUI Interface

```bash
python subgrab_gui.py
# Windows:
start_subgrab_gui.bat
```

The GUI provides:
- Domain input and scan configuration
- API Keys tab with fields for all services and direct "Get Key" links
- Save / Load configuration to `api_keys.json`
- Real-time scrolling output window
- Direct access to results folder

---

## Troubleshooting

### Certificate Transparency returns fewer results than expected

crt.sh rate-limits heavy users. The module retries up to 3 times with exponential backoff (10s → 20s → 40s) and falls back to 4 independent CT sources (CertSpotter, Entrust, tls.bufferover.run, urlscan.io) — all run regardless of crt.sh status, so a rate-limit never zeros out the total.

### No results from C99

C99 results require a public scan to exist for your domain within the last 14 days. If no scan is found, the tool automatically falls back to DNSdumpster then HackerTarget.

### Google returns empty results

Google frequently blocks automated requests. The search engine module will log a warning and continue — other sources are unaffected.

### DNS brute force is slow

Reduce permutation size by using a shorter wordlist and lowering thread count if you hit DNS rate limits:
```bash
python subgrab.py example.com --wordlist small.txt --threads 20
```

### AI returns no subdomains

- Grok: verify the key at [console.x.ai](https://console.x.ai) and check your credit balance
- OpenRouter: check [openrouter.ai](https://openrouter.ai) dashboard for balance and rate limits
- Both require at least 3 discovered subdomains to enter pattern-analysis mode

### "401 Unauthorized" from any API

The API key is invalid or expired. Re-generate it from the provider's console.

### "429 Too Many Requests"

Rate limit hit. Use `--stealth` to add delays, or wait before re-running.

### Windows encoding errors in reports

The tool writes all files with `encoding='utf-8'`. Open reports in an editor that supports UTF-8 (VS Code, Notepad++, etc.).

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-source`)
3. Add your scanner module in `modules/` following the template above
4. Test against a domain you own or have permission to enumerate
5. Submit a pull request with a clear description

For bug reports, open an issue on GitHub.

---

## License

MIT License — see [LICENSE.txt](LICENSE.txt) for full text.

**Use only on domains you own or have explicit written permission to test.**  
The authors accept no liability for misuse.

---

**Author:** Krishnendu Paul — [GitHub](https://github.com/bidhata/SubGrab) | [LinkedIn](https://www.linkedin.com/in/krishpaul/)
