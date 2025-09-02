# SubGrab - Advanced Subdomain Enumeration Tool


**Python** | **MIT License** | **Cross-Platform**

🚀 **Next-Generation Subdomain Discovery with AI-Powered Intelligence**

SubGrab is a high-performance, multi-threaded subdomain enumeration tool designed for security researchers, penetration testers, and bug bounty hunters. Enhanced with **OpenRouter AI integration**, it combines traditional reconnaissance techniques with advanced artificial intelligence to uncover subdomains that other tools might miss.

---

## 🌟 Why Choose SubGrab?

SubGrab stands out with its robust feature set and AI-driven capabilities, making it an essential tool for comprehensive subdomain discovery:

- 🤖 **AI-Powered Discovery**: Leverages OpenRouter API with multiple AI models for intelligent subdomain generation.
- 🔄 **Multi-Source Enumeration**: Combines 15+ discovery techniques for maximum coverage.
- ⚡ **High Performance**: Multi-threaded architecture with intelligent rate limiting.
- 🎯 **Comprehensive Coverage**: Combines passive and active reconnaissance methods.
- 📊 **Rich Output**: Supports multiple export formats with detailed reporting.
- 🖥️ **User-Friendly**: Offers both CLI and GUI interfaces.
- 🔒 **Security-Focused**: Includes built-in subdomain takeover detection.
- 📱 **Cross-Platform**: Compatible with Windows, Linux, and macOS.

---

## ✨ Features

### 🔍 Discovery Capabilities
- **Certificate Transparency Logs**: Queries crt.sh and CertSpotter for historical and current certificates.
- **DNS Enumeration**: Supports brute force, SRV records, and zone transfers.
- **Web Archives**: Extracts subdomains from Wayback Machine and other archives.
- **Search Engine Reconnaissance**: Uses Google dorks and other search engines for indexed subdomains.
- **Security APIs**: Integrates with VirusTotal, SecurityTrails, Censys, and Shodan for enriched data.
- **GitHub Code Search**: Analyzes code repositories for subdomain leaks.
- **RapidDNS Database**: Leverages public DNS data for fast discovery.
- **Reverse DNS Lookups**: Maps IPs to domains for additional insights.
- 🤖 **AI-Powered Generation**: Uses OpenRouter to intelligently generate subdomain candidates.

### 🛡️ Security Analysis
- **Subdomain Takeover Detection**: Identifies vulnerabilities across 50+ services (e.g., AWS S3, GitHub Pages, Heroku).
- **SSH Service Detection**: Scans for open SSH services on port 22.
- **HTTP/HTTPS Status Verification**: Checks for live subdomains and their status codes.
- **Wildcard DNS Detection**: Identifies wildcard DNS configurations to avoid false positives.
- **Port Scanning Integration**: Detects common services (HTTP, HTTPS, FTP, SMTP) and their versions.

### 📊 Output & Reporting
- **Multiple Formats**: Exports results in TXT, CSV, JSON, and HTML.
- **Interactive HTML Reports**: Includes charts and statistics for easy analysis.
- **Real-time Progress Tracking**: Displays live scan updates.
- **Detailed Vulnerability Reports**: Highlights security findings like takeover risks.
- **Tool Compatibility**: Exports results compatible with Nmap and Masscan.

### ⚙️ Advanced Options
- **Multi-threading**: Configurable threads (1-200) for performance tuning.
- **Proxy Support**: Supports HTTP, HTTPS, and SOCKS proxies for stealth and bypassing rate limits.
- **Custom Wordlists**: Allows user-defined wordlists for DNS brute forcing.
- **Rate Limiting & Stealth Mode**: Minimizes detection with random delays and throttling.
- **Custom DNS Servers**: Supports user-specified DNS resolvers.
- **Timeout Configuration**: Adjustable request timeouts for flexibility.

---

## 🤖 AI Integration

SubGrab's **OpenRouter API integration** enhances subdomain discovery with cutting-edge AI capabilities.

### 🧠 Supported AI Models
| Model                | Provider   | Best For                   | Performance | Cost   |
|----------------------|------------|----------------------------|-------------|--------|
| Claude 3.5 Sonnet    | Anthropic  | Best overall               | ⭐⭐⭐⭐⭐ | Medium |
| Claude 3 Haiku       | Anthropic  | Fast & cost-effective      | ⭐⭐⭐⭐  | Low    |
| GPT-4o               | OpenAI     | High-quality analysis      | ⭐⭐⭐⭐⭐ | High   |
| GPT-4o Mini          | OpenAI     | Balanced performance       | ⭐⭐⭐⭐  | Medium |
| Gemini Pro 1.5       | Google     | Good alternative           | ⭐⭐⭐⭐  | Medium |
| Llama 3.1 8B         | Meta       | Open source option         | ⭐⭐⭐   | Low    |

### 🎯 AI Workflow
1. **Traditional Discovery**: Gathers initial subdomains using passive and active methods.
2. **Pattern Analysis**: AI analyzes discovered subdomains to identify naming patterns, numbering schemes, and environments.
3. **Intelligent Generation**: Generates new subdomain candidates based on observed patterns (e.g., if `api1` exists, suggests `api2`, `api3`).
4. **Quality Validation**: Filters AI-generated candidates for relevance and likelihood before DNS testing.

### 🎯 AI Capabilities
- 📊 **Pattern Recognition**: Identifies naming conventions and organizational patterns.
- 🧠 **Intelligent Variations**: Suggests logical extensions based on existing subdomains.
- 🏢 **Context Awareness**: Considers organization type and industry-specific patterns.
- 🔍 **Quality Validation**: Ensures high-probability subdomain candidates.
- ⚡ **Efficiency**: Activates AI analysis only when sufficient data (3+ subdomains) is available.

---

## 🛠️ Installation

### 📦 Method 1: Python Installation
```bash
# Clone the repository
git clone https://github.com/bidhata/SubGrab.git
cd SubGrab

# Install dependencies
pip install -r requirements.txt

# Run SubGrab
python subgrab.py example.com
```

### 💻 Method 2: Windows Binaries (Recommended)
1. Download the latest release from [Releases](https://github.com/bidhata/SubGrab/releases).
2. Extract the ZIP file.
3. Double-click `QuickStart.bat` for an interactive menu, or run `subgrab.exe example.com` directly.

### 🐳 Method 3: Docker
```bash
# Build Docker image
docker build -t subgrab .

# Run with Docker
docker run -v $(pwd)/results:/app/results subgrab example.com
```

---

## 🚀 Quick Start

### 🎯 Basic Usage
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

### 🤖 AI-Enhanced Scanning
```bash
# AI with Claude 3.5 Sonnet
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3.5-sonnet

# Cost-effective with Claude Haiku
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model anthropic/claude-3-haiku

# Maximum coverage with multiple APIs
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --shodan-key YOUR_SHODAN_KEY \
  --virustotal-key YOUR_VT_KEY
```

### 🖥️ GUI Usage
```bash
# Launch GUI
python subgrab_gui.py

# Or on Windows
subgrab_gui.exe
```

---

## 📖 Usage

### 🎛️ Command Line Options
```bash
usage: subgrab.py [-h] [--threads THREADS] [--timeout TIMEOUT] [--fast] [--stealth]
                  [--proxy-file PROXY_FILE] [--wordlist WORDLIST] [--nameservers NAMESERVERS]
                  [--openrouter-key OPENROUTER_KEY] [--openrouter-model OPENROUTER_MODEL]
                  [--shodan-key SHODAN_KEY] [--securitytrails-key SECURITYTRAILS_KEY]
                  [--virustotal-key VIRUSTOTAL_KEY] [--censys-id CENSYS_ID]
                  [--censys-secret CENSYS_SECRET] [--github-token GITHUB_TOKEN]
                  domain

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

### 📝 Usage Examples
#### 🎯 Basic Enumeration
```bash
# Simple scan
python subgrab.py example.com

# With custom wordlist
python subgrab.py example.com --wordlist /path/to/wordlist.txt

# Using custom DNS servers
python subgrab.py example.com --nameservers 1.1.1.1 8.8.8.8
```

#### 🤖 AI-Enhanced Scanning
```bash
# AI pattern analysis
python subgrab.py example.com --openrouter-key sk-or-xxxxx

# Specific AI model
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --openrouter-model openai/gpt-4o
```

#### ⚡ Performance Optimization
```bash
# High-speed scanning
python subgrab.py example.com --threads 200 --timeout 10

# Stealth mode
python subgrab.py example.com --stealth --threads 10
```

#### 🔑 Multiple API Keys
```bash
python subgrab.py example.com \
  --openrouter-key sk-or-xxxxx \
  --shodan-key YOUR_SHODAN_KEY \
  --virustotal-key YOUR_VT_KEY \
  --securitytrails-key YOUR_ST_KEY \
  --censys-id YOUR_CENSYS_ID \
  --censys-secret YOUR_CENSYS_SECRET \
  --github-token YOUR_GITHUB_TOKEN
```

---

## 🔧 Configuration

### 🤖 OpenRouter Setup
1. Visit [openrouter.ai](https://openrouter.ai).
2. Sign up and add $5-10 credits.
3. Generate an API key.
4. Use the key with `--openrouter-key sk-or-xxxxx`.

### 🔑 API Keys Configuration
Create `api_keys.json`:
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

### 📝 Custom Wordlists
```bash
# Example wordlist (custom_subdomains.txt)
www
api
dev
staging
admin
mail
ftp
```

### 🌐 Proxy Configuration
```bash
# Proxy file format (proxies.txt)
http://proxy1:8080
https://user:pass@proxy2:3128
socks5://proxy3:1080
```

---

## 📊 Output Formats

### 📁 Output Directory Structure
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

### 📄 Report Contents
#### 📋 Text Reports
- Complete subdomain lists with status.
- Categorized by response type.
- Security findings (e.g., takeovers, SSH).
- Statistics and summaries.

#### 📊 JSON Report
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

#### 🌐 HTML Report
Interactive dashboard with:
- 📈 Statistics charts.
- 🗺️ Discovery method breakdown.
- 🔍 Searchable subdomain table.
- ⚠️ Security findings.
- 📊 Response time analysis.

---

## 🎛️ API Integrations

| Service          | Purpose                  | Free Tier        | Rate Limit        |
|------------------|--------------------------|------------------|-------------------|
| OpenRouter       | AI subdomain generation  | ❌               | Model dependent   |
| Shodan           | Infrastructure discovery | ✅ Limited       | 1 req/sec         |
| VirusTotal       | Domain intelligence      | ✅ 4 req/min     | 4 req/min         |
| SecurityTrails   | DNS history             | ✅ 50 req/month  | Varies            |
| Censys           | Certificate data        | ✅ 250 req/month | 0.2 req/sec       |
| GitHub           | Code search             | ✅ 5000 req/hour | 30 req/min        |

---

## 🖥️ GUI Interface

### 🎯 Features
- 📝 **Easy Configuration**: Point-and-click setup.
- 📊 **Real-time Progress**: Live scan updates.
- 🔑 **API Key Management**: Save/load configurations.
- 📁 **Result Management**: Direct access to reports.
- 🎨 **Modern Interface**: Clean and intuitive design.

### 🚀 Usage
```bash
python subgrab_gui.py
# Or on Windows
subgrab_gui.exe
```

---

## 💻 Windows Binaries

### 📦 Package Contents
- `subgrab.exe`: Command-line version (213 MB).
- `subgrab_gui.exe`: GUI version (29 MB).
- `QuickStart.bat`, `run_cli.bat`, `run_gui.bat`: Easy launchers.
- Complete documentation and examples.

### 🚀 Quick Start (Windows)
1. Download the latest release ZIP.
2. Extract to a folder.
3. Run `QuickStart.bat` and choose GUI or CLI mode.

---

## 🔍 Discovery Methods

### 🌐 Passive Methods
- **Certificate Transparency**: Queries crt.sh and CertSpotter.
- **DNS Intelligence**: Brute forcing, SRV records, zone transfers, reverse DNS.
- **Web Archives**: Wayback Machine and Archive.today for historical data.
- **Search Engines**: Google, Bing, DuckDuckGo with advanced operators.
- **Security APIs**: VirusTotal, SecurityTrails, Censys, Shodan.
- **Code Repositories**: GitHub and GitLab code search.

### 🎯 Active Methods
- **HTTP/HTTPS Probing**: Status code verification, technology fingerprinting.
- **Port Scanning**: SSH, HTTP, HTTPS, FTP, SMTP detection.

### 🤖 AI-Powered Methods
- **Intelligent Generation**: Context-aware subdomain suggestions.
- **Pattern Analysis**: Identifies naming conventions and environments.

---

## 🛡️ Security Features

### 🎯 Subdomain Takeover Detection
- **Supported Services**: AWS S3, Azure, GitHub Pages, Heroku, Netlify, and 50+ others.
- **Detection Methods**: DNS resolution, HTTP response analysis, SSL certificate validation.

### 🔒 Security Best Practices
- Authorized testing only.
- Rate limiting and stealth mode for responsible scanning.
- Proxy support for anonymity.
- Comprehensive logging for audit trails.

---

## 📈 Performance

### ⚡ Benchmarks
| Metric              | Traditional Tools | SubGrab | SubGrab + AI |
|---------------------|-------------------|---------|--------------|
| Subdomains Found    | 200-300           | 400-600 | 600-800      |
| Execution Time      | 5-10 min          | 3-7 min | 5-10 min     |
| False Positives     | 10-15%            | 5-8%    | 2-5%         |
| Unique Discoveries  | Standard          | Enhanced| AI-Enhanced   |

---

## 🤝 Contributing

We welcome contributions from the security community! To contribute:
1. Fork the repository.
2. Create a feature branch.
3. Make changes and test thoroughly.
4. Submit a pull request with clear documentation.

See the [Contributing](#contributing) section in the original documentation for detailed guidelines.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

### ⚖️ Terms of Use
- ✅ Use only for authorized testing.
- ✅ Follow responsible disclosure practices.
- ❌ Do not use for malicious purposes.
- ❌ No warranty; use at your own risk.

---

## 📞 Contact & Support

**Author**: Krishnendu Paul  
**GitHub**: [bidhata/SubGrab](https://github.com/bidhata/SubGrab)  
**Support**: Open an issue on GitHub or contact the author for assistance.

⭐ **If SubGrab helped you, please give it a star!** ⭐  
Made with ❤️ for the Security Community.

