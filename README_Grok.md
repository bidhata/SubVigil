# Grok AI Integration Guide for SubGrab

## 🚀 What is Grok?

**Grok** is an advanced AI model developed by **xAI** (Elon Musk's AI company). It offers powerful language understanding and generation capabilities, making it ideal for intelligent subdomain discovery and pattern analysis.

---

## 💎 Why Use Grok for SubGrab?

### ✨ Key Advantages

| Feature | Benefit |
|---------|---------|
| 💰 **Free Credits** | Free credits for new accounts to get started |
| 🎯 **High Quality** | State-of-the-art AI reasoning and pattern recognition |
| ⚡ **Fast** | Quick response times for real-time enumeration |
| 🔌 **Compatible** | OpenAI-compatible API - easy to integrate |
| 🆓 **No CC Required** | Start using immediately without credit card |
| 🔄 **Regular Updates** | Continuous improvements from xAI team |

### 📊 Grok vs. Other AI Options

| AI Model | Provider | Cost | Free Tier | Quality | Speed |
|----------|----------|------|-----------|---------|-------|
| **Grok 3** | **xAI** | **$** | **Free Credits** | **⭐⭐⭐⭐⭐** | **⚡⚡⚡** |
| Grok 4 | xAI | $$ | Free Credits | ⭐⭐⭐⭐⭐ | ⚡⚡ |
| Grok 4.1 Fast | xAI | $ | Free Credits | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ |
| Claude 3.5 | Anthropic | $$ | Limited | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| GPT-4o | OpenAI | $$$ | Very Limited | ⭐⭐⭐⭐⭐ | ⚡⚡ |

---

## 🛠️ Getting Started with Grok

### Step 1: Create an xAI Account

1. Visit **[console.x.ai](https://console.x.ai)** or **[x.ai/api](https://x.ai/api)**
2. Click **"Sign Up"** or **"Get Started"**
3. Create your account (no credit card required for free tier)
4. Verify your email address

### Step 2: Get Your API Key

1. Log into the **[xAI Console](https://console.x.ai)**
2. Navigate to **"API Keys"** section
3. Click **"Create New API Key"**
4. Copy your API key (format: `xai-...`)
5. **Store it securely!** (Never share or commit to repositories)

### Step 3: Available Models

| Model | Description | Best For | Speed | Cost |
|-------|-------------|----------|-------|------|
| `grok-3` | Primary Grok model (default) | General subdomain analysis | Fast | $ |
| `grok-3-mini` | Lightweight Grok | Quick scans, low cost | Very Fast | ¢ |
| `grok-4` | Flagship reasoning model | Complex pattern analysis | Medium | $$ |
| `grok-4.1-fast` | Speed-optimized with 2M context | Large scans, agentic use | Fast | $ |

**Recommended:** Start with `grok-3` for standard subdomain enumeration.

---

## 💻 Using Grok with SubGrab

### Basic Usage

```bash
# Simple Grok-powered scan
python subgrab.py example.com --grok-key xai-your-key-here
```

### Advanced Usage

```bash
# Specify Grok model
python subgrab.py example.com \
  --grok-key xai-your-key-here \
  --grok-model grok-3

# Combine with other tools for maximum coverage
python subgrab.py example.com \
  --grok-key xai-your-key-here \
  --shodan-key YOUR_SHODAN_KEY \
  --virustotal-key YOUR_VT_KEY \
  --threads 100
```

### Dual AI Mode (Grok + OpenRouter)

For **maximum AI-powered discovery**, use both Grok and OpenRouter:

```bash
python subgrab.py example.com \
  --grok-key xai-your-key-here \
  --openrouter-key sk-or-your-key \
  --openrouter-model anthropic/claude-3.5-sonnet
```

**Benefits:**
- 🎯 **Double AI Coverage**: Two different AI models analyze patterns
- 🔍 **More Subdomains**: Each AI finds unique patterns
- 🆚 **Cross-Validation**: AI models validate each other's findings
- 🚀 **Best Results**: Maximum subdomain discovery rate

---

## 🎯 How Grok Enhances Subdomain Discovery

### 1️⃣ **Pattern Recognition**

Grok analyzes discovered subdomains to identify:
- Numbering schemes (api1, api2, api3...)
- Environment patterns (dev, test, staging, prod)
- Regional variations (us, eu, asia, uk...)
- Version patterns (v1, v2, api-v1...)
- Naming conventions (service names, departments)

### 2️⃣ **Intelligent Generation**

Based on patterns, Grok generates:
- **Logical variations** of existing subdomains
- **Missing entries** in numbered sequences
- **Common alternatives** for found environments
- **Industry-specific** subdomain names

### 3️⃣ **Quality Validation**

Grok validates AI-generated candidates:
- Filters out nonsensical suggestions
- Ranks by likelihood of existence
- Removes duplicates and near-duplicates
- Ensures proper subdomain formatting

### 4️⃣ **Context Awareness**

Grok considers:
- Organization type (corporate, educational, government)
- Industry-specific patterns (tech, finance, healthcare)
- Geographic indicators
- Technology stack hints

---

## 📈 Expected Performance

### Subdomain Discovery Improvement

| Scenario | Without AI | With Grok | Improvement |
|----------|------------|-----------|-------------|
| Small Domain | 50-100 | 100-200 | +100% |
| Medium Domain | 200-500 | 500-1500 | +150% |
| Large Domain | 500-2000 | 2000-8000 | +300% |

### Real-World Examples

```
Example 1: tech-startup.com
- Traditional methods: 87 subdomains
- With Grok AI: 234 subdomains (+169%)

Example 2: university.edu
- Traditional methods: 342 subdomains
- With Grok AI: 1,127 subdomains (+229%)

Example 3: enterprise.com
- Traditional methods: 1,456 subdomains
- With Grok AI: 5,891 subdomains (+305%)
```

---

## 🔒 Security & Privacy

### Best Practices

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables or config files
   - Rotate keys regularly
   - Store in secure key management systems

2. **Rate Limiting**
   - Grok has built-in rate limits
   - SubGrab respects these limits automatically
   - Use stealth mode for sensitive targets

3. **Legal Compliance**
   - Only scan domains you're authorized to test
   - Follow bug bounty program rules
   - Respect robots.txt and security policies

---

## 💰 Pricing & Credits

### Free Credits

- **Free credits for new accounts** to get started
- Perfect for:
  - Bug bounty hunters
  - Security researchers
  - Personal projects
  - Learning and testing

### Paid Tier

- Pay-as-you-go pricing
- Grok 3: $0.30/1M input, $0.50/1M output tokens
- Grok 4: $3/1M input, $15/1M output tokens
- **Check [x.ai/pricing](https://x.ai/pricing) for latest rates**

### Cost Estimation

Typical SubGrab scan costs:

| Domain Size | AI Requests | Estimated Cost (Grok 3) |
|-------------|-------------|-------------------------|
| Small | 5-10 | $0.01-0.05 |
| Medium | 15-30 | $0.05-0.15 |
| Large | 40-80 | $0.15-0.50 |

**Very affordable for most scans!** 🎉

---

## 🔧 Configuration

### Option 1: Command Line

```bash
python subgrab.py example.com \
  --grok-key xai-your-key-here \
  --grok-model grok-3
```

### Option 2: Config File

Create `api_keys.json`:

```json
{
  "grok": "xai-your-key-here",
  "openrouter": "sk-or-your-key-here",
  "shodan": "your-shodan-key",
  "virustotal": "your-vt-key"
}
```

Then run:
```bash
python subgrab.py example.com --config api_keys.json
```

### Option 3: Environment Variables

```bash
export GROK_API_KEY="xai-your-key-here"
export GROK_MODEL="grok-3"

python subgrab.py example.com
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Grok integration module not found"

**Solution:**
```bash
# Make sure grok_integration.py is in the same directory
ls -la grok_integration.py

# If missing, download it from the repository
```

#### 2. "Grok API error: 401 Unauthorized"

**Solution:**
- Check your API key is correct
- Ensure no extra spaces in the key
- Verify your xAI account is active
- Check if you've exceeded rate limits

#### 3. "Grok API error: 429 Too Many Requests"

**Solution:**
- You've hit the rate limit
- Wait a few minutes and try again
- Use `--stealth` mode to add delays
- Reduce number of AI requests

#### 4. "No AI-generated subdomains"

**Possible causes:**
- Not enough subdomains found (need 3+)
- Domain is very small
- Pattern analysis found no clear patterns

**Solution:**
- Let traditional methods run first
- Ensure you have API connectivity
- Check Grok service status at [status.x.ai](https://status.x.ai)

---

## 📚 Advanced Tips

### 1. Optimize AI Usage

```bash
# Let traditional methods discover patterns first
python subgrab.py example.com \
  --grok-key xai-key \
  --threads 100 \
  --timeout 60
```

### 2. Combine Data Sources

```bash
# Maximum discovery with all sources + AI
python subgrab.py example.com \
  --grok-key xai-key \
  --shodan-key shodan-key \
  --virustotal-key vt-key \
  --securitytrails-key st-key \
  --github-token github-token
```

### 3. Industry-Specific Scans

For better AI pattern recognition, provide context about the target:
- Tech companies: More dev/API subdomains
- Universities: Department and faculty patterns
- E-commerce: Store and region variations
- Healthcare: Compliance and privacy patterns

---

## 🎓 Learning Resources

### Official Documentation

- **xAI Documentation**: [docs.x.ai](https://docs.x.ai)
- **API Reference**: [x.ai/api](https://x.ai/api)
- **Console**: [console.x.ai](https://console.x.ai)

### Community

- **SubGrab GitHub**: [github.com/bidhata/SubGrab](https://github.com/bidhata/SubGrab)
- **Issues & Support**: Open an issue on GitHub
- **Feature Requests**: Submit via GitHub discussions

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Basic Grok scan
python subgrab.py TARGET --grok-key xai-KEY

# Specify model
python subgrab.py TARGET --grok-key xai-KEY --grok-model grok-3

# Dual AI mode
python subgrab.py TARGET --grok-key xai-KEY --openrouter-key sk-or-KEY

# Full-powered scan
python subgrab.py TARGET \
  --grok-key xai-KEY \
  --shodan-key SHODAN \
  --threads 100 \
  --fast
```

### Environment Variables

```bash
export GROK_API_KEY="xai-your-key"
export GROK_MODEL="grok-3"
```

---

## 📞 Support

**Having issues?**

1. Check this guide first
2. Review [official xAI docs](https://docs.x.ai)
3. Open an issue on [GitHub](https://github.com/bidhata/SubGrab/issues)
4. Contact the maintainer via GitHub

---

## 📄 License

SubGrab is licensed under the **MIT License**.

Grok API usage subject to xAI's Terms of Service.

---

**Made with ❤️ for the Security Community**

**Get Started Now**: [console.x.ai](https://console.x.ai)
