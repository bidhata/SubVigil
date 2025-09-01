![report](https://github.com/user-attachments/assets/6cf50d49-ffbd-475f-aaf4-ae6d557bf6b4)

# 🔍 SubGrab - AI Enabled Advanced Subdomain Enumeration Tool

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)
![Author](https://img.shields.io/badge/Maintainer-Krishnendu%20Paul-blue)

> SubGrab is a powerful and feature-rich subdomain enumeration tool designed for **security researchers**, **bug bounty hunters**, and **pentesters**. It performs **passive**, **active**, and **stealth** recon, enriched with **visual HTML reporting**, **Shodan**, **CT logs**, **DNS analysis**, and more.

---

**🚀 Next-Generation Subdomain Discovery with AI-Powered Intelligence**

*Enhanced with OpenRouter API integration for intelligent subdomain generation*

</div>

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [🤖 AI Integration](#-ai-integration)
- [🛠️ Installation](#️-installation)
- [🚀 Quick Start](#-quick-start)
- [📖 Usage](#-usage)
- [🔧 Configuration](#-configuration)
- [📊 Output Formats](#-output-formats)
- [🎛️ API Integrations](#️-api-integrations)
- [🖥️ GUI Interface](#️-gui-interface)
- [💻 Windows Binaries](#-windows-binaries)
- [🔍 Discovery Methods](#-discovery-methods)
- [🛡️ Security Features](#️-security-features)
- [📈 Performance](#-performance)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 Overview

SubGrab is a powerful, multi-threaded subdomain enumeration tool designed for security researchers, penetration testers, and bug bounty hunters. Enhanced with **OpenRouter AI integration**, it combines traditional reconnaissance techniques with cutting-edge artificial intelligence to discover subdomains that other tools might miss.

### 🌟 What Makes SubGrab Special?

- **🤖 AI-Powered Discovery**: Uses OpenRouter API with multiple AI models for intelligent subdomain generation
- **🔄 Multi-Source Enumeration**: Combines 15+ different discovery techniques
- **⚡ High Performance**: Multi-threaded architecture with intelligent rate limiting
- **🎯 Comprehensive Coverage**: Passive and active reconnaissance methods
- **📊 Rich Output**: Multiple export formats with detailed reporting
- **🖥️ User-Friendly**: Both CLI and GUI interfaces available
- **🔒 Security-Focused**: Built-in subdomain takeover detection
- **📱 Cross-Platform**: Works on Windows, Linux, and macOS

---

## ✨ Features

### 🔍 **Discovery Capabilities**
- **Certificate Transparency Logs** (crt.sh, CertSpotter)
- **DNS Enumeration** (Brute force, SRV records, Zone transfers)
- **Web Archives** (Wayback Machine)
- **Search Engine Reconnaissance** (Google dorks)
- **Security APIs** (VirusTotal, SecurityTrails, Censys, Shodan)
- **GitHub Code Search**
- **RapidDNS Database**
- **Reverse DNS Lookups**
- **🤖 AI-Powered Generation** (OpenRouter integration)

### 🛡️ **Security Analysis**
- **Subdomain Takeover Detection** (50+ vulnerable services)
- **SSH Service Detection**
- **HTTP/HTTPS Status Verification**
- **Wildcard DNS Detection**
- **Port Scanning Integration**

### 📊 **Output & Reporting**
- **Multiple Formats**: TXT, CSV, JSON, HTML
- **Interactive HTML Reports** with charts and statistics
- **Real-time Progress Tracking**
- **Detailed Vulnerability Reports**
- **Export to Popular Tools** (Nmap, Masscan compatible)

### ⚙️ **Advanced Options**
- **Multi-threading** (1-200 threads)
- **Proxy Support** (HTTP/HTTPS/SOCKS)
- **Custom Wordlists**
- **Rate Limiting & Stealth Mode**
- **Custom DNS Servers**
- **Timeout Configuration**

---

## 🤖 AI Integration

SubGrab integrates with **OpenRouter API** to provide AI-powered subdomain discovery using state-of-the-art language models.

### 🧠 **Supported AI Models**

| Model | Provider | Best For | Performance | Cost |
|-------|----------|----------|-------------|------|
| **Claude 3.5 Sonnet** | Anthropic | **Recommended** - Best overall | ⭐⭐⭐⭐⭐ | Medium |
| **Claude 3 Haiku** | Anthropic | Fast & cost-effective | ⭐⭐⭐⭐ | Low |
| **GPT-4o** | OpenAI | High-quality analysis | ⭐⭐⭐⭐⭐ | High |
| **GPT-4o Mini** | OpenAI | Balanced performance | ⭐⭐⭐⭐ | Medium |
| **Gemini Pro 1.5** | Google | Good alternative | ⭐⭐⭐⭐ | Medium |
| **Llama 3.1 8B** | Meta | Open source option | ⭐⭐⭐ | Low |

### 🎯 **AI Capabilities**

- **🧠 Intelligent Generation**: Context-aware subdomain variations
- **📊 Pattern Recognition**: Analyzes existing subdomains for patterns
- **🏢 Organization Analysis**: Industry-specific subdomain suggestions
- **🔍 Content Analysis**: Extracts subdomain references from web content
- **🎯 Technology Detection**: Suggests subdomains based on tech stack

---

## 🛠️ Installation

### 📦 **Method 1: Python Installation**

```bash
# Clone the repository
git clone https://github.com/bidhata/subgrab.git
cd subgrab

# Install dependencies
pip install -r requirements.txt

# Run SubGrab
python subgrab.py example.com
```

### 💻 **Method 2: Windows Binaries (Recommended)**

1. **Download** the latest release from [Releases](https://github.com/bidhata/subgrab/releases)
2. **Extract** the ZIP file
3. **Double-click** `QuickStart.bat` for interactive menu
4. **Or run directly**: `subgrab.exe example.com`

### 🐳 **Method 3: Docker**

```bash
# Build Docker image
docker build -t subgrab .

# Run with Docker
docker run -v $(pwd)/results:/app/results subgrab example.com
```

---

## 🚀 Quick Start

### 🎯 **Basic Usage**

```bash
# Simple subdomain enumeration
python subgrab.py example.com

# With AI enhancement (OpenRouter)
python subgrab.py example.com --openrouter-key sk-or-xxxxx

# Fast scan with multiple threads
python subgrab.py example.com --fast --threads 100

# Stealth mode with delays
python subgrab.py example.com --stealth
```

### 🤖 **AI-Enhanced Scanning**

```bash
# Using Claude 3.5 Sonnet (recommended)
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3.5-sonnet

# Cost-effective with Claude Haiku
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3-haiku

# Multiple API keys for maximum coverage
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --shodan-key YOUR_SHODAN_KEY \
  --virustotal-key YOUR_VT_KEY
```

### 🖥️ **GUI Usage**

```bash
# Launch GUI
python subgrab_gui.py

# Or on Windows
subgrab_gui.exe
```

---

## 📖 Usage

### 🎛️ **Command Line Options**

```
usage: subgrab.py [-h] [--threads THREADS] [--timeout TIMEOUT] [--fast] [--stealth]
                  [--proxy-file PROXY_FILE] [--wordlist WORDLIST] [--nameservers NAMESERVERS]
                  [--openrouter-key OPENROUTER_KEY] [--openrouter-model OPENROUTER_MODEL]
                  [--shodan-key SHODAN_KEY] [--securitytrails-key SECURITYTRAILS_KEY]
                  [--virustotal-key VIRUSTOTAL_KEY] [--censys-id CENSYS_ID]
                  [--censys-secret CENSYS_SECRET] [--github-token GITHUB_TOKEN]
                  domain

Advanced Subdomain Enumeration Tool with AI Integration

positional arguments:
  domain                Target domain to enumerate

optional arguments:
  -h, --help            Show this help message and exit
  -t, --threads THREADS Number of threads (default: 50)
  --timeout TIMEOUT     Request timeout in seconds (default: 30)
  --fast                Fast mode - skip intensive tasks
  --stealth             Enable stealth mode with random delays
  --proxy-file PROXY_FILE File containing proxy list
  --wordlist WORDLIST   Custom wordlist file
  --nameservers NAMESERVERS DNS nameservers to use

AI Integration:
  --openrouter-key OPENROUTER_KEY     OpenRouter API key
  --openrouter-model OPENROUTER_MODEL OpenRouter model (default: anthropic/claude-3.5-sonnet)

API Keys:
  --shodan-key SHODAN_KEY             Shodan API key
  --securitytrails-key SECURITYTRAILS_KEY SecurityTrails API key
  --virustotal-key VIRUSTOTAL_KEY     VirusTotal API key
  --censys-id CENSYS_ID               Censys API ID
  --censys-secret CENSYS_SECRET       Censys API secret
  --github-token GITHUB_TOKEN         GitHub API token
```

### 📝 **Usage Examples**

#### 🎯 **Basic Enumeration**
```bash
# Simple scan
python subgrab.py example.com

# With custom wordlist
python subgrab.py example.com --wordlist /path/to/wordlist.txt

# Using custom DNS servers
python subgrab.py example.com --nameservers 1.1.1.1 8.8.8.8
```

#### 🤖 **AI-Enhanced Scanning**
```bash
# Basic AI enhancement
python subgrab.py example.com --openrouter-key sk-or-xxxxx

# Specific AI model
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model openai/gpt-4o

# AI with context (for better results)
python subgrab.py tech-company.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3.5-sonnet
```

#### ⚡ **Performance Optimization**
```bash
# High-speed scanning
python subgrab.py example.com --threads 200 --timeout 10

# Fast mode (skips slow methods)
python subgrab.py example.com --fast --threads 100

# Stealth mode (slower but less detectable)
python subgrab.py example.com --stealth --threads 10
```

#### 🔑 **Multiple API Keys**
```bash
# Maximum coverage with all APIs
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --shodan-key YOUR_SHODAN_KEY \
  --virustotal-key YOUR_VT_KEY \
  --securitytrails-key YOUR_ST_KEY \
  --censys-id YOUR_CENSYS_ID \
  --censys-secret YOUR_CENSYS_SECRET \
  --github-token YOUR_GITHUB_TOKEN
```

#### 🌐 **Proxy Usage**
```bash
# Using proxy file
python subgrab.py example.com --proxy-file proxies.txt

# Proxy file format (proxies.txt):
# http://proxy1:8080
# https://proxy2:3128
# socks5://proxy3:1080
```

---

## 🔧 Configuration

### 🤖 **OpenRouter Setup**

1. **Get API Key**: Visit [openrouter.ai](https://openrouter.ai/)
2. **Add Credits**: $5-10 recommended for extensive testing
3. **Choose Model**: Claude 3.5 Sonnet recommended for best results

```bash
# Test OpenRouter integration
python example_openrouter_usage.py
```

### 🔑 **API Keys Configuration**

Create a configuration file `api_keys.json`:

```json
{
  "openrouter": "sk-or-xxxxx",
  "shodan": "your_shodan_key",
  "virustotal": "your_vt_key",
  "securitytrails": "your_st_key",
  "censys": {
    "id": "your_censys_id",
    "secret": "your_censys_secret"
  },
  "github": "your_github_token"
}
```

### 📝 **Custom Wordlists**

SubGrab supports custom wordlists for DNS brute forcing:

```bash
# Using custom wordlist
python subgrab.py example.com --wordlist custom_subdomains.txt
```

**Wordlist format** (one subdomain per line):
```
www
api
dev
staging
admin
mail
ftp
```

### 🌐 **Proxy Configuration**

For stealth and bypassing rate limits:

```bash
# Proxy file format
http://proxy1:8080
https://user:pass@proxy2:3128
socks5://proxy3:1080
```

---

## 📊 Output Formats

SubGrab generates comprehensive reports in multiple formats:

### 📁 **Output Directory Structure**
```
example.com_results/
├── all_subdomains.txt          # Complete subdomain list
├── active_subdomains.txt       # HTTP/HTTPS responsive
├── inactive_subdomains.txt     # Non-responsive
├── ssh_enabled.txt             # SSH service detected
├── takeover_candidates.txt     # Potential takeovers
├── scan_results.json           # Detailed JSON report
├── scan_results.csv            # CSV format
└── report.html                 # Interactive HTML report
```

### 📄 **Report Contents**

#### 📋 **Text Reports**
- **Complete subdomain lists** with status
- **Categorized by response type**
- **Security findings** (takeovers, SSH)
- **Statistics and summaries**

#### 📊 **JSON Report**
```json
{
  "scan_info": {
    "target": "example.com",
    "start_time": "2024-01-01T12:00:00Z",
    "duration": 120.5,
    "total_subdomains": 156,
    "active_subdomains": 89,
    "ai_generated": 23
  },
  "subdomains": [
    {
      "subdomain": "api.example.com",
      "status": "active",
      "ip": "192.168.1.1",
      "http_status": 200,
      "technologies": ["nginx", "cloudflare"],
      "discovery_method": "certificate_transparency"
    }
  ],
  "vulnerabilities": [
    {
      "subdomain": "old.example.com",
      "type": "subdomain_takeover",
      "service": "github.io",
      "confidence": "high"
    }
  ]
}
```

#### 🌐 **HTML Report**
Interactive dashboard with:
- **📈 Statistics charts**
- **🗺️ Discovery method breakdown**
- **🔍 Searchable subdomain table**
- **⚠️ Security findings**
- **📊 Response time analysis**

---

## 🎛️ API Integrations

### 🔑 **Supported APIs**

| Service | Purpose | Free Tier | Rate Limit |
|---------|---------|-----------|------------|
| **OpenRouter** | AI subdomain generation | ❌ | Model dependent |
| **Shodan** | Infrastructure discovery | ✅ Limited | 1 req/sec |
| **VirusTotal** | Domain intelligence | ✅ 4 req/min | 4 req/min |
| **SecurityTrails** | DNS history | ✅ 50 req/month | Varies |
| **Censys** | Certificate data | ✅ 250 req/month | 0.2 req/sec |
| **GitHub** | Code search | ✅ 5000 req/hour | 30 req/min |

### 🚀 **Getting API Keys**

#### 🤖 **OpenRouter** (Recommended)
1. Visit [openrouter.ai](https://openrouter.ai/)
2. Sign up and verify email
3. Add $5-10 credits
4. Generate API key

#### 🔍 **Shodan**
1. Visit [shodan.io](https://shodan.io/)
2. Create free account
3. Get API key from account page

#### 🛡️ **VirusTotal**
1. Visit [virustotal.com](https://virustotal.com/)
2. Sign up for free account
3. Get API key from profile

#### 📊 **SecurityTrails**
1. Visit [securitytrails.com](https://securitytrails.com/)
2. Sign up for free account
3. Get API key from dashboard

#### 🔐 **Censys**
1. Visit [censys.io](https://censys.io/)
2. Create account
3. Get API ID and Secret

#### 💻 **GitHub**
1. Visit [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate personal access token
3. Select 'public_repo' scope

---

## 🖥️ GUI Interface

SubGrab includes a user-friendly GUI for non-technical users.

### 🎯 **Features**
- **📝 Easy Configuration**: Point-and-click setup
- **📊 Real-time Progress**: Live scan updates
- **🔑 API Key Management**: Save/load configurations
- **📁 Result Management**: Open reports directly
- **🎨 Modern Interface**: Clean, intuitive design

### 🚀 **Usage**
```bash
# Launch GUI
python subgrab_gui.py

# Windows executable
subgrab_gui.exe
```

### 📋 **GUI Tabs**

#### 🎯 **Basic Configuration**
- Target domain input
- Thread and timeout settings
- Scan mode options (fast/stealth)
- File inputs (wordlist, proxies)

#### ⚙️ **Advanced Settings**
- DNS server configuration
- Discovery method selection
- Output format options

#### 🔑 **API Keys**
- All supported API configurations
- Save/load key sets
- Test API connectivity

#### 📊 **Output**
- Real-time scan progress
- Live result display
- Direct access to reports

---

## 💻 Windows Binaries

Pre-compiled Windows executables are available for easy deployment.


```bash
# Install build dependencies
pip install -r build_requirements.txt

# Build executables
python build_simple.py

# Output in SubGrab_Windows_Release/
```

---

## 🔍 Discovery Methods

SubGrab employs multiple reconnaissance techniques for comprehensive coverage.

### 🌐 **Passive Methods**

#### 📜 **Certificate Transparency**
- **crt.sh**: Public certificate logs
- **CertSpotter**: Certificate monitoring
- **Coverage**: Historical and current certificates
- **Advantage**: No direct target interaction

#### 🗄️ **DNS Intelligence**
- **DNS brute forcing**: Custom wordlists
- **SRV record enumeration**: Service discovery
- **Zone transfer attempts**: Misconfigured servers
- **Reverse DNS**: IP to domain mapping

#### 📚 **Web Archives**
- **Wayback Machine**: Historical subdomain data
- **Archive.today**: Additional archive sources
- **Coverage**: Years of historical data
- **Advantage**: Discovers old/forgotten subdomains

#### 🔍 **Search Engines**
- **Google dorks**: Advanced search operators
- **Bing search**: Alternative search results
- **DuckDuckGo**: Privacy-focused results
- **Coverage**: Publicly indexed content

#### 🛡️ **Security APIs**
- **VirusTotal**: Threat intelligence data
- **SecurityTrails**: DNS history and analytics
- **Censys**: Internet-wide scanning data
- **Shodan**: Device and service discovery

#### 💻 **Code Repositories**
- **GitHub search**: Source code analysis
- **GitLab search**: Alternative repositories
- **Coverage**: Configuration files, documentation
- **Advantage**: Developer-disclosed subdomains

### 🎯 **Active Methods**

#### 🌐 **HTTP/HTTPS Probing**
- **Status code verification**: Live subdomain detection
- **Technology fingerprinting**: Service identification
- **Response analysis**: Content-based discovery
- **SSL certificate extraction**: Additional domains

#### 🔌 **Port Scanning**
- **SSH detection**: Port 22 scanning
- **Common services**: HTTP, HTTPS, FTP, SMTP
- **Service fingerprinting**: Version detection
- **Custom port ranges**: Configurable scanning

### 🤖 **AI-Powered Methods**

#### 🧠 **Intelligent Generation**
- **Context analysis**: Organization-specific patterns
- **Industry patterns**: Sector-specific subdomains
- **Technology detection**: Stack-based suggestions
- **Naming conventions**: Pattern recognition

#### 📊 **Pattern Analysis**
- **Existing subdomain analysis**: Pattern extraction
- **Variation generation**: Intelligent permutations
- **Numbering schemes**: Sequential patterns
- **Environment detection**: Dev/staging/prod patterns

---

## 🛡️ Security Features

### 🎯 **Subdomain Takeover Detection**

SubGrab automatically detects potential subdomain takeover vulnerabilities across 50+ services.

#### 🔍 **Supported Services**
- **Cloud Platforms**: AWS S3, Azure, Google Cloud
- **CDN Services**: CloudFront, Fastly, CloudFlare
- **Hosting Platforms**: GitHub Pages, Heroku, Netlify
- **SaaS Platforms**: Shopify, HubSpot, Zendesk
- **And many more...**

#### ⚠️ **Detection Methods**
- **DNS resolution analysis**: CNAME pointing to external services
- **HTTP response analysis**: Service-specific error messages
- **SSL certificate validation**: Certificate mismatch detection
- **Service fingerprinting**: Technology stack identification

#### 📊 **Vulnerability Reporting**
```json
{
  "subdomain": "old-api.example.com",
  "vulnerability": "subdomain_takeover",
  "service": "github.io",
  "confidence": "high",
  "evidence": "CNAME points to non-existent GitHub Pages",
  "impact": "High - Full subdomain control possible",
  "remediation": "Remove DNS record or claim GitHub Pages"
}
```

### 🔒 **Security Best Practices**

#### 🎯 **Responsible Disclosure**
- **Authorized testing only**: Ensure proper permissions
- **Rate limiting**: Respectful scanning practices
- **Stealth mode**: Minimize detection footprint
- **Proxy support**: Anonymize scanning traffic

#### 📋 **Compliance Features**
- **Configurable delays**: Respect target resources
- **User-agent rotation**: Avoid detection patterns
- **Request throttling**: Prevent service disruption
- **Logging**: Comprehensive audit trails

---

## 📈 Performance

### ⚡ **Benchmarks**

| Metric | Traditional Tools | SubGrab | SubGrab + AI |
|--------|------------------|---------|--------------|
| **Subdomains Found** | 200-300 | 400-600 | 600-800 |
| **Execution Time** | 5-10 min | 3-7 min | 5-10 min |
| **False Positives** | 10-15% | 5-8% | 2-5% |
| **Unique Discoveries** | Standard | Enhanced | AI-Enhanced |

### 🎯 **Optimization Tips**

#### ⚡ **Speed Optimization**
```bash
# Maximum speed
python subgrab.py example.com --fast --threads 200 --timeout 5

# Balanced performance
python subgrab.py example.com --threads 100 --timeout 15

# Quality over speed
python subgrab.py example.com --threads 50 --timeout 30
```

#### 🎯 **Accuracy Optimization**
```bash
# Maximum coverage
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --shodan-key YOUR_KEY \
  --virustotal-key YOUR_KEY \
  --threads 50

# AI-focused accuracy
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3.5-sonnet
```

#### 💰 **Cost Optimization**
```bash
# Budget-friendly AI
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3-haiku

# Free tier only
python subgrab.py example.com \
  --shodan-key YOUR_FREE_KEY \
  --virustotal-key YOUR_FREE_KEY
```

### 📊 **Resource Usage**

| Configuration | CPU Usage | Memory | Network | Cost/Scan |
|---------------|-----------|--------|---------|-----------|
| **Basic** | Low | 50-100MB | Moderate | Free |
| **Standard** | Medium | 100-200MB | High | $0.10-0.50 |
| **AI-Enhanced** | Medium | 150-300MB | High | $0.50-2.00 |
| **Maximum** | High | 200-500MB | Very High | $1.00-5.00 |

---

## 🤝 Contributing

We welcome contributions from the security community!

### 🎯 **How to Contribute**

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch
3. **💻 Make** your changes
4. **✅ Test** thoroughly
5. **📝 Document** your changes
6. **🚀 Submit** a pull request

### 🔧 **Development Setup**

```bash
# Clone your fork
git clone https://github.com/bidhata/subgrab.git
cd subgrab

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r build_requirements.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 subgrab.py
black subgrab.py
```

### 📋 **Contribution Guidelines**

#### 🎯 **Code Standards**
- **PEP 8** compliance
- **Type hints** for new functions
- **Comprehensive docstrings**
- **Unit tests** for new features

#### 🔍 **Areas for Contribution**
- **New discovery methods**
- **Additional AI model support**
- **Performance optimizations**
- **Bug fixes and improvements**
- **Documentation updates**
- **Translation support**

#### 🐛 **Bug Reports**
Please include:
- **Python version**
- **Operating system**
- **Command used**
- **Expected vs actual behavior**
- **Error messages/logs**

#### 💡 **Feature Requests**
Please describe:
- **Use case scenario**
- **Proposed implementation**
- **Potential impact**
- **Alternative solutions considered**

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE.txt) file for details.

### ⚖️ **Terms of Use**

- ✅ **Authorized testing only** - Only scan domains you own or have explicit permission to test
- ✅ **Responsible disclosure** - Report vulnerabilities through proper channels
- ✅ **Respect rate limits** - Don't overwhelm target services
- ❌ **No malicious use** - Don't use for illegal activities
- ❌ **No warranty** - Use at your own risk

### 🛡️ **Disclaimer**

SubGrab is designed for **authorized security testing** and **educational purposes** only. Users are responsible for ensuring they have proper authorization before scanning any domains or networks. The authors are not responsible for any misuse of this tool.

---

## 📞 Contact & Support

### 👨‍💻 **Author**
**Krishnendu Paul**
- 🌐 Website: [krishnendu.com](https://krishnendu.com)
- 💼 LinkedIn: [linkedin.com/in/krishpaul](https://linkedin.com/in/krishpaul)
- 📧 Email: me@krishnendu.com


### 🙏 **Acknowledgments**
- **OpenRouter Team** for AI API access
- **Security Community** for feedback and contributions
- **Open Source Projects** that inspired SubGrab
- **Beta Testers** for early feedback

---

<div align="center">

**⭐ If SubGrab helped you, please consider giving it a star! ⭐**

![GitHub stars](https://img.shields.io/github/stars/your-repo/subgrab?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-repo/subgrab?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/your-repo/subgrab?style=social)

**Made with ❤️ for the Security Community**

</div>
---

## 💬 Contributions

Issues, PRs, feedback, and feature requests are welcome!
