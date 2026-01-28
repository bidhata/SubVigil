# 🚀 SubGrab + Grok Quick Reference Card

## 1-Minute Setup

```bash
# 1. Get FREE Grok API key from: https://console.x.ai
# 2. Run your first AI-powered scan:
python subgrab.py example.com --grok-key xai-YOUR-KEY
```

---

## Essential Commands

### Basic Scans
```bash
# FREE AI scan with Grok
python subgrab.py target.com --grok-key xai-KEY

# Fast mode
python subgrab.py target.com --grok-key xai-KEY --fast --threads 100

# Stealth mode
python subgrab.py target.com --grok-key xai-KEY --stealth
```

### Advanced Scans
```bash
# Dual AI (Grok + OpenRouter) - Maximum Coverage
python subgrab.py target.com \
  --grok-key xai-KEY \
  --openrouter-key sk-or-KEY

# Full-powered with all APIs
python subgrab.py target.com \
  --grok-key xai-KEY \
  --shodan-key SHODAN \
  --virustotal-key VT \
  --threads 100
```

---

## Command-Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--grok-key` | xAI Grok API key (FREE) | `xai-abc123` |
| `--grok-model` | Grok model to use | `grok-beta` |
| `--openrouter-key` | OpenRouter API key | `sk-or-abc123` |
| `--openrouter-model` | OpenRouter model | `anthropic/claude-3.5-sonnet` |
| `--fast` | Skip intensive tasks | - |
| `--stealth` | Add random delays | - |
| `--threads` | Number of threads | `50` (default) |
| `--timeout` | Request timeout (sec) | `30` (default) |

---

## API Key Configuration

Edit `shodan.json`:
```json
{
  "grok": "xai-YOUR-KEY",
  "openrouter": "sk-or-YOUR-KEY",
  "shodan": "",
  "virustotal": "",
  "securitytrails": "",
  "censys_id": "",
  "censys_secret": "",
  "github": ""
}
```

---

## Output Files

After scan completes, check `example.com_results/`:

| File | Contains |
|------|----------|
| `all_subdomains.txt` | Complete list |
| `active_subdomains.txt` | HTTP/HTTPS responsive |
| `inactive_subdomains.txt` | Non-responsive |
| `ssh_enabled.txt` | SSH services found |
| `takeover_candidates.txt` | Potential takeovers |
| `scan_results.json` | Detailed JSON report |
| `scan_results.csv` | CSV format |
| `report.html` | Interactive HTML report |

---

## Grok Models

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| `grok-beta` | General use ⭐ Recommended | ⚡⚡⚡ | FREE |
| `grok-vision-beta` | Complex patterns | ⚡⚡ | FREE |

---

## Quick Decision Tree

```
Need AI enhancement?
├─ YES
│  ├─ Want FREE? → Use Grok
│  ├─ Want BEST quality? → Use Claude (OpenRouter)
│  └─ Want MAXIMUM coverage? → Use BOTH
└─ NO → Use built-in methods only (--fast)
```

---

## Troubleshooting

### "Grok integration module not found"
```bash
# Make sure grok_integration.py is in the same directory
ls -la grok_integration.py
```

### "401 Unauthorized"
- Check API key is correct
- No spaces in the key
- Account is active

### "429 Too Many Requests"
- Hit rate limit
- Wait a few minutes
- Use `--stealth` mode

### "No AI-generated subdomains"
- Need 3+ subdomains for pattern analysis
- Check API connectivity
- Verify at status.x.ai

---

## Performance Expectations

| Target Size | Subdomains Without AI | With Grok | Improvement |
|-------------|----------------------|-----------|-------------|
| Small | 50-100 | 100-200 | +100% |
| Medium | 200-500 | 500-1500 | +150% |
| Large | 500-2000 | 2000-8000 | +300% |

---

## Cost (Grok FREE Tier)

**$25 FREE credits/month = Approximately:**
- 200+ small scans
- 50-100 medium scans
- 25-30 large scans

**Most users stay FREE!** 🎉

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main documentation |
| `README_Grok.md` | Detailed Grok guide |
| `AI_COMPARISON.md` | AI options comparison |
| `CHANGELOG.md` | Version history |
| `GROK_INTEGRATION_SUMMARY.md` | Integration summary |

---

## Support

- **Get Grok API**: https://console.x.ai
- **GitHub Issues**: https://github.com/bidhata/SubGrab/issues
- **Author**: Krishnendu Paul [@bidhata]

---

## Pro Tips

💡 **Use config file** instead of typing keys every time  
💡 **Start with Grok** (it's FREE!)  
💡 **Add OpenRouter** for critical engagements  
💡 **Use `--fast`** for quick recon  
💡 **Enable `--stealth`** for sensitive targets  

---

## One-Liners

```bash
# Quick scan
python subgrab.py example.com --grok-key xai-KEY

# Pro scan
python subgrab.py example.com --grok-key xai-KEY --openrouter-key sk-or-KEY --threads 100

# Full power
python subgrab.py example.com --grok-key xai-KEY --shodan-key SHODAN --virustotal-key VT --fast
```

---

**Version:** 2.1.0 | **Date:** 2026-01-28

**Made with ❤️ for the Security Community**
